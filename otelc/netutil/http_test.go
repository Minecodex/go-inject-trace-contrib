package netutil

import (
	"net/url"
	"testing"
)

func TestHTTPServerEndpoint(t *testing.T) {
	for _, test := range []struct {
		input string
		host  string
		port  int
	}{
		{"https://api.example.com/v1/chat", "api.example.com", 443},
		{"http://127.0.0.1:8080/v1/messages", "127.0.0.1", 8080},
		{"http://[::1]/v1/messages", "::1", 80},
		{"https://[2001:db8::1]:8443/v1/chat", "2001:db8::1", 8443},
		{"http://example.com:0", "example.com", 0},
		{"http://example.com:99999", "example.com", 0},
		{"custom://example.com", "example.com", 0},
		{"/relative", "", 0},
	} {
		t.Run(test.input, func(t *testing.T) {
			u, err := url.Parse(test.input)
			if err != nil {
				t.Fatal(err)
			}
			host, port := HTTPServerEndpoint(u)
			if host != test.host || port != test.port {
				t.Fatalf("endpoint = %s:%d, want %s:%d", host, port, test.host, test.port)
			}
		})
	}
	if host, port := HTTPServerEndpoint(nil); host != "" || port != 0 {
		t.Fatalf("nil URL returned %s:%d", host, port)
	}
}
