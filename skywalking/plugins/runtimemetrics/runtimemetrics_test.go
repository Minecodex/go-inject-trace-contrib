package runtimemetrics

import (
	"testing"

	"github.com/apache/skywalking-go/plugins/core/operator"
)

func TestConfiguredExclusionPreventsRuntimeInstrumentRegistration(t *testing.T) {
	oldOperator, oldAppender, oldHook := operator.GetOperator, operator.MetricsAppender, operator.MetricsCollectAppender
	t.Cleanup(func() {
		operator.GetOperator, operator.MetricsAppender, operator.MetricsCollectAppender = oldOperator, oldAppender, oldHook
	})
	operator.GetOperator = func() operator.Operator { return nil }
	for _, test := range []struct {
		name     string
		excludes string
		enabled  bool
	}{
		{"default", "", true},
		{"excluded", "runtimemetrics", false},
		{"excluded-in-list", "http,runtimemetrics,grpc", false},
		{"other-plugin", "http", true},
		{"similar-name", "my-runtimemetrics", true},
	} {
		t.Run(test.name, func(t *testing.T) {
			t.Setenv("SW_AGENT_PLUGIN_EXCLUDES", test.excludes)
			registered, hooks := 0, 0
			operator.MetricsAppender = func(interface{}) { registered++ }
			operator.MetricsCollectAppender = func(func()) { hooks++ }
			registerMetrics()
			if test.enabled {
				if registered == 0 || hooks != 1 {
					t.Fatalf("runtime instruments missing: meters=%d hooks=%d", registered, hooks)
				}
			} else if registered != 0 || hooks != 0 {
				t.Fatalf("excluded collector registered meters=%d hooks=%d", registered, hooks)
			}
		})
	}
}
