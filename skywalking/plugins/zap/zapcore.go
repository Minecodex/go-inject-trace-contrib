//go:build goinject

//inject:go.uber.org/zap/zapcore
package zap

import (
	"fmt"

	"github.com/kakj-go/go-inject-trace-contrib/skywalking/logbridge"
)

type CheckedEntry struct {
	//inject:add
	SWContext interface{}
	//inject:add
	SWContextField *Field
	//inject:add
	SWFields []Field
}

func (entry *CheckedEntry) Write(fields ...Field) {
	if entry != nil && logbridge.Enabled("zap") {
		if reporter := logbridge.Reporter(); logbridge.ReporterEnabled() && reporter != nil && entry.SWContext != nil {
			labels := make(map[string]string)
			for _, key := range logbridge.LabelKeys() {
				for _, field := range fields {
					if field.Key == key {
						swZapLabel(labels, field)
					}
				}
			}
			for _, field := range entry.SWFields {
				swZapLabel(labels, field)
			}
			reporter.ReportLog(entry.SWContext, entry.Time, entry.Level.String(), entry.Message, labels)
		}
		if logbridge.TracingEnabled() && entry.SWContextField != nil {
			fields = append(fields, *entry.SWContextField)
		}
	}
}

//inject:add
func swZapLabel(labels map[string]string, field Field) {
	if field.Interface != nil {
		labels[field.Key] = fmt.Sprintf("%v", field.Interface)
	} else if field.Integer > 0 {
		labels[field.Key] = fmt.Sprintf("%d", field.Integer)
	} else if field.String != "" {
		labels[field.Key] = field.String
	}
}
