// Package logbridge shares the official logger configuration and operator
// binding without introducing dependencies on either logging framework.
package logbridge

import (
	"os"
	"strconv"
	"strings"
	"sync"

	"github.com/apache/skywalking-go/plugins/core/operator"
)

var pending struct {
	sync.Mutex
	logger operator.LogOperator
}

func Enabled(framework string) bool {
	kind := os.Getenv("SW_AGENT_LOG_TYPE")
	return kind == "" || kind == "auto" || kind == framework
}

func flag(name string, fallback bool) bool {
	value, exists := os.LookupEnv(name)
	if !exists {
		return fallback
	}
	parsed, err := strconv.ParseBool(value)
	if err != nil {
		return fallback
	}
	return parsed
}

func TracingEnabled() bool  { return flag("SW_AGENT_LOG_TRACING_ENABLE", true) }
func ReporterEnabled() bool { return flag("SW_AGENT_LOG_REPORTER_ENABLE", true) }

func ContextKey() string {
	if key := os.Getenv("SW_AGENT_LOG_TRACING_KEY"); key != "" {
		return key
	}
	return "SW_CTX"
}

func LabelKeys() []string {
	var keys []string
	for _, key := range strings.Split(os.Getenv("SW_AGENT_LOG_REPORTER_LABEL_KEYS"), ",") {
		if key = strings.TrimSpace(key); key != "" {
			keys = append(keys, key)
		}
	}
	return keys
}

func Reporter() operator.LogReporter {
	current := operator.GetOperator()
	if current == nil {
		return nil
	}
	reporter, _ := current.LogReporter().(operator.LogReporter)
	return reporter
}

func Context(withEndpoint bool) interface{} {
	if reporter := Reporter(); reporter != nil {
		return reporter.GetLogContext(withEndpoint)
	}
	return nil
}

func Register(logger operator.LogOperator) {
	pending.Lock()
	pending.logger = logger
	pending.Unlock()
	Bind()
}

// Bind also runs when the tracer boots: framework globals are often created
// before the injected main initializer establishes the SDK operator.
func Bind() {
	current := operator.GetOperator()
	if current == nil {
		return
	}
	pending.Lock()
	logger := pending.logger
	pending.Unlock()
	if logger == nil {
		return
	}
	if change, ok := current.Logger().(interface{ ChangeLogger(operator.LogOperator) }); ok {
		change.ChangeLogger(logger)
	}
}
