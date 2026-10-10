// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

// Package netutil provides shared network parsing helpers.
package netutil

import (
	"net/url"
	"strconv"
	"strings"
)

// HTTPServerEndpoint matches the pinned upstream endpoint semantics,
// including default HTTP/HTTPS ports and bare IPv6 host names.
func HTTPServerEndpoint(u *url.URL) (string, int) {
	if u == nil {
		return "", 0
	}
	address := u.Hostname()
	if address == "" {
		return "", 0
	}
	if text := u.Port(); text != "" {
		port, err := strconv.ParseUint(text, 10, 16)
		if err != nil || port == 0 {
			return address, 0
		}
		return address, int(port)
	}
	switch strings.ToLower(u.Scheme) {
	case "http":
		return address, 80
	case "https":
		return address, 443
	default:
		return address, 0
	}
}
