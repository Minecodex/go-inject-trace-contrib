// The pinned Apache mock collector records telemetry but does not implement
// the agent's background control RPCs. This isolated test gateway returns an
// empty Commands message for those RPCs and forwards all telemetry unchanged.
package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"net"
	"os"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
)

type wireCodec struct{}

func (wireCodec) Name() string { return "proto" }
func (wireCodec) Marshal(value any) ([]byte, error) {
	if frame, ok := value.(*[]byte); ok {
		return *frame, nil
	}
	return nil, fmt.Errorf("unexpected wire frame %T", value)
}
func (wireCodec) Unmarshal(data []byte, value any) error {
	frame, ok := value.(*[]byte)
	if !ok {
		return fmt.Errorf("unexpected wire frame %T", value)
	}
	*frame = append((*frame)[:0], data...)
	return nil
}

func gateway(upstream *grpc.ClientConn) grpc.StreamHandler {
	return func(_ any, downstream grpc.ServerStream) error {
		method, _ := grpc.MethodFromServerStream(downstream)
		switch method {
		case "/skywalking.v3.ConfigurationDiscoveryService/fetchConfigurations",
			"/skywalking.v3.ProfileTask/getProfileTaskCommands",
			"/skywalking.v10.PprofTask/getPprofTaskCommands":
			var request []byte
			if err := downstream.RecvMsg(&request); err != nil {
				return err
			}
			// An empty protobuf Commands message means no configuration changes
			// or profiling tasks. It neither acknowledges nor fabricates telemetry.
			response := []byte{}
			return downstream.SendMsg(&response)
		}
		ctx, cancel := context.WithCancel(downstream.Context())
		defer cancel()
		if headers, ok := metadata.FromIncomingContext(ctx); ok {
			ctx = metadata.NewOutgoingContext(ctx, headers.Copy())
		}
		stream, err := upstream.NewStream(ctx, &grpc.StreamDesc{
			ServerStreams: true, ClientStreams: true,
		}, method, grpc.ForceCodec(wireCodec{}))
		if err != nil {
			return err
		}
		go func() {
			for {
				var frame []byte
				if err := downstream.RecvMsg(&frame); err != nil {
					if err == io.EOF {
						_ = stream.CloseSend()
					} else {
						cancel()
					}
					return
				}
				if err := stream.SendMsg(&frame); err != nil {
					return // RecvMsg below preserves the upstream RPC status.
				}
			}
		}()
		headers, err := stream.Header()
		if err != nil {
			return err
		}
		if err := downstream.SendHeader(headers); err != nil {
			return err
		}
		defer func() { downstream.SetTrailer(stream.Trailer()) }()
		for {
			var frame []byte
			if err := stream.RecvMsg(&frame); err != nil {
				if err == io.EOF {
					return nil
				}
				return err
			}
			if err := downstream.SendMsg(&frame); err != nil {
				return err
			}
		}
	}
}

func main() {
	listen := flag.String("listen", ":19877", "isolated Docker network listener")
	target := flag.String("upstream", "127.0.0.1:19876", "real mock collector")
	flag.Parse()
	connection, err := grpc.NewClient(*target, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err == nil {
		defer connection.Close()
		var listener net.Listener
		listener, err = net.Listen("tcp", *listen)
		if err == nil {
			server := grpc.NewServer(grpc.ForceServerCodec(wireCodec{}),
				grpc.UnknownServiceHandler(gateway(connection)))
			err = server.Serve(listener)
		}
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
