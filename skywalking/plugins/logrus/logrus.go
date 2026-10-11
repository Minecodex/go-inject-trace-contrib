//go:build goinject

//inject:github.com/sirupsen/logrus
package logrus

import (
	"fmt"

	"github.com/kakj-go/go-inject-trace-contrib/skywalking/logbridge"
)

type Logger struct{}

func New() (__injectResult0 *Logger) {
	defer func() { swUpdateLogrus(__injectResult0) }()
}

func (logger *Logger) SetFormatter(formatter Formatter) {
	defer func() { swUpdateLogrus(logger) }()
}

//inject:add
func swUpdateLogrus(logger *Logger) {
	if logger == nil || !logbridge.Enabled("logrus") {
		return
	}
	if logbridge.TracingEnabled() {
		if _, wrapped := logger.Formatter.(*swLogrusFormatter); !wrapped {
			logger.Formatter = &swLogrusFormatter{base: logger.Formatter}
		}
	}
	logbridge.Register(&swLogrusAdapter{entry: logger.WithFields(Fields{})})
}

//inject:add
type swLogrusFormatter struct{ base Formatter }

//inject:add
func (formatter *swLogrusFormatter) Format(entry *Entry) ([]byte, error) {
	context := logbridge.Context(logbridge.ReporterEnabled())
	if reporter := logbridge.Reporter(); logbridge.ReporterEnabled() && reporter != nil && context != nil {
		labels := make(map[string]string)
		for _, key := range logbridge.LabelKeys() {
			if value, exists := entry.Data[key]; exists {
				labels[key] = fmt.Sprintf("%v", value)
			}
		}
		reporter.ReportLog(context, entry.Time, entry.Level.String(), entry.Message, labels)
	}
	if stringer, ok := context.(fmt.Stringer); ok {
		entry.Data[logbridge.ContextKey()] = stringer.String()
	}
	return formatter.base.Format(entry)
}

//inject:add
type swLogrusAdapter struct{ entry *Entry }

//inject:add
func (adapter *swLogrusAdapter) WithField(key string, value interface{}) interface{} {
	return &swLogrusAdapter{entry: adapter.entry.WithField(key, value)}
}

//inject:add
func (adapter *swLogrusAdapter) Info(args ...interface{}) { adapter.entry.Info(args...) }

//inject:add
func (adapter *swLogrusAdapter) Infof(format string, args ...interface{}) {
	adapter.entry.Infof(format, args...)
}

//inject:add
func (adapter *swLogrusAdapter) Warn(args ...interface{}) { adapter.entry.Warn(args...) }

//inject:add
func (adapter *swLogrusAdapter) Warnf(format string, args ...interface{}) {
	adapter.entry.Warnf(format, args...)
}

//inject:add
func (adapter *swLogrusAdapter) Error(args ...interface{}) { adapter.entry.Error(args...) }

//inject:add
func (adapter *swLogrusAdapter) Errorf(format string, args ...interface{}) {
	adapter.entry.Errorf(format, args...)
}
