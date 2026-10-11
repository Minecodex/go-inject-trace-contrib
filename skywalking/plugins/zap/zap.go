//go:build goinject

//inject:go.uber.org/zap
package zap

import (
	"fmt"

	"github.com/kakj-go/go-inject-trace-contrib/skywalking/logbridge"
	"go.uber.org/zap/zapcore"
)

type Logger struct {
	//inject:add
	SWFields []zapcore.Field
}

func New(core zapcore.Core, options ...Option) (__injectResult0 *Logger) {
	defer func() {
		if __injectResult0 != nil && logbridge.Enabled("zap") {
			logbridge.Register(&swZapAdapter{logger: __injectResult0})
		}
	}()
}

func (logger *Logger) check(level zapcore.Level, message string) (__injectResult0 *zapcore.CheckedEntry) {
	defer func() {
		if __injectResult0 == nil || !logbridge.Enabled("zap") {
			return
		}
		__injectResult0.SWFields = logger.SWFields
		if logbridge.ReporterEnabled() || logbridge.TracingEnabled() {
			context := logbridge.Context(logbridge.ReporterEnabled())
			__injectResult0.SWContext = context
			if stringer, ok := context.(fmt.Stringer); ok {
				field := String(logbridge.ContextKey(), stringer.String())
				__injectResult0.SWContextField = &field
			}
		}
	}()
}

func (logger *Logger) With(fields ...Field) (__injectResult0 *Logger) {
	defer func() {
		if __injectResult0 == nil {
			return
		}
		var selected []zapcore.Field
		for _, key := range logbridge.LabelKeys() {
			for _, field := range fields {
				if field.Key == key {
					selected = append(selected, field)
				}
			}
		}
		__injectResult0.SWFields = append(selected, logger.SWFields...)
	}()
}

//inject:add
type swZapAdapter struct{ logger *Logger }

//inject:add
func (adapter *swZapAdapter) WithField(key string, value interface{}) interface{} {
	return &swZapAdapter{logger: adapter.logger.With(Any(key, value))}
}

//inject:add
func (adapter *swZapAdapter) Info(args ...interface{}) { adapter.logger.Info(fmt.Sprint(args...)) }

//inject:add
func (adapter *swZapAdapter) Infof(format string, args ...interface{}) {
	adapter.logger.Info(fmt.Sprintf(format, args...))
}

//inject:add
func (adapter *swZapAdapter) Warn(args ...interface{}) { adapter.logger.Warn(fmt.Sprint(args...)) }

//inject:add
func (adapter *swZapAdapter) Warnf(format string, args ...interface{}) {
	adapter.logger.Warn(fmt.Sprintf(format, args...))
}

//inject:add
func (adapter *swZapAdapter) Error(args ...interface{}) { adapter.logger.Error(fmt.Sprint(args...)) }

//inject:add
func (adapter *swZapAdapter) Errorf(format string, args ...interface{}) {
	adapter.logger.Error(fmt.Sprintf(format, args...))
}
