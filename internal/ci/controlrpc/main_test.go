package main

import (
	"context"
	"io"
	"net"
	"testing"
	"time"

	commands "github.com/apache/skywalking-go/protocols/collect/common/v3"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
)

func serve(t *testing.T, handler grpc.StreamHandler) *grpc.ClientConn {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server := grpc.NewServer(grpc.ForceServerCodec(wireCodec{}), grpc.UnknownServiceHandler(handler))
	go func() { _ = server.Serve(listener) }()
	t.Cleanup(server.Stop)
	client, err := grpc.NewClient(listener.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = client.Close() })
	return client
}

func TestControlCommandsAndTransparentCollector(t *testing.T) {
	upstream := serve(t, func(_ any, stream grpc.ServerStream) error {
		method, _ := grpc.MethodFromServerStream(stream)
		if method != "/telemetry.Collector/collect" {
			return status.Error(codes.Unimplemented, "unsupported real collector method")
		}
		headers, _ := metadata.FromIncomingContext(stream.Context())
		if len(headers.Get("fixture-id")) != 1 || headers.Get("fixture-id")[0] != "real-frames" {
			return status.Error(codes.InvalidArgument, "metadata was changed")
		}
		_ = stream.SendHeader(metadata.Pairs("collector", "actual"))
		stream.SetTrailer(metadata.Pairs("receipt", "unaltered"))
		for {
			var frame []byte
			if err := stream.RecvMsg(&frame); err != nil {
				if err == io.EOF {
					return nil
				}
				return err
			}
			if err := stream.SendMsg(&frame); err != nil {
				return err
			}
		}
	})
	client := serve(t, gateway(upstream))
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	for _, method := range []string{
		"/skywalking.v3.ConfigurationDiscoveryService/fetchConfigurations",
		"/skywalking.v3.ProfileTask/getProfileTaskCommands",
		"/skywalking.v10.PprofTask/getPprofTaskCommands",
	} {
		request, response := []byte{10, 3, 'a', 'p', 'p'}, []byte(nil)
		if err := client.Invoke(ctx, method, &request, &response, grpc.ForceCodec(wireCodec{})); err != nil {
			t.Fatal(err)
		}
		var decoded commands.Commands
		if err := proto.Unmarshal(response, &decoded); err != nil || len(decoded.Commands) != 0 {
			t.Fatalf("invalid empty control response: %x, %v", response, err)
		}
	}
	ctx = metadata.NewOutgoingContext(ctx, metadata.Pairs("fixture-id", "real-frames"))
	stream, err := client.NewStream(ctx, &grpc.StreamDesc{ClientStreams: true, ServerStreams: true},
		"/telemetry.Collector/collect", grpc.ForceCodec(wireCodec{}))
	if err != nil {
		t.Fatal(err)
	}
	frames := [][]byte{{10, 3, 'o', 'n', 'e'}, {10, 3, 't', 'w', 'o'}}
	for _, frame := range frames {
		if err := stream.SendMsg(&frame); err != nil {
			t.Fatal(err)
		}
	}
	_ = stream.CloseSend()
	for _, expected := range frames {
		var actual []byte
		if err := stream.RecvMsg(&actual); err != nil || string(actual) != string(expected) {
			t.Fatalf("collector frame changed: %x != %x, %v", actual, expected, err)
		}
	}
	var final []byte
	if err := stream.RecvMsg(&final); err != io.EOF {
		t.Fatalf("RPC did not complete: %v", err)
	}
	header, _ := stream.Header()
	if header.Get("collector")[0] != "actual" || stream.Trailer().Get("receipt")[0] != "unaltered" {
		t.Fatal("collector response metadata was changed")
	}
	request, response := []byte{}, []byte(nil)
	err = client.Invoke(ctx, "/unsupported/collect", &request, &response, grpc.ForceCodec(wireCodec{}))
	if status.Code(err) != codes.Unimplemented || status.Convert(err).Message() != "unsupported real collector method" {
		t.Fatalf("upstream failure was hidden: %v", err)
	}
}
