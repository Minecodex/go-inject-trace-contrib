package logbridge

import (
	"testing"

	core "github.com/apache/skywalking-go/plugins/core"
	"github.com/apache/skywalking-go/plugins/core/operator"
)

type fixtureLogger struct{}

func (*fixtureLogger) WithField(string, interface{}) interface{} { return nil }
func (*fixtureLogger) Info(...interface{})                       {}
func (*fixtureLogger) Infof(string, ...interface{})              {}
func (*fixtureLogger) Warn(...interface{})                       {}
func (*fixtureLogger) Warnf(string, ...interface{})              {}
func (*fixtureLogger) Error(...interface{})                      {}
func (*fixtureLogger) Errorf(string, ...interface{})             {}

func TestLoggerCreatedBeforeTracerBootBindsAfterInitialization(t *testing.T) {
	original := operator.GetOperator
	defer func() { operator.GetOperator = original }()
	tracer := &core.Tracer{}
	operator.GetOperator = func() operator.Operator { return tracer }
	logger := &fixtureLogger{}
	// Logger returns a typed nil LogWrapper until the SDK tracer boots.
	Register(logger)
	tracer.Log = &core.LogWrapper{Logger: &fixtureLogger{}}
	Bind()
	if tracer.Log.Logger != logger {
		t.Fatal("pre-boot logger was not bound after tracer initialization")
	}
}
