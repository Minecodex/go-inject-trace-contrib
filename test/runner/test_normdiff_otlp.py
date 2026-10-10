import unittest

from normdiff_otlp import canon_metrics, canon_traces


def payload(path, sdk_name="opentelemetry"):
    return {"resourceSpans": [{
        "resource": {"attributes": [{"key": "telemetry.sdk.name", "value": {"stringValue": sdk_name}}]},
        "scopeSpans": [{"scope": {"name": "http"}, "spans": [{
            "traceId": "trace", "spanId": "span", "name": "GET", "kind": 2,
            "attributes": [{"key": "url.path", "value": {"stringValue": path}}],
        }]}],
    }]}


class TelemetryNormalizationTests(unittest.TestCase):
    def test_readiness_polling_cannot_leave_an_empty_trace(self):
        self.assertEqual(canon_traces(payload("/health")), canon_traces({}))

    def test_business_spans_remain_required(self):
        self.assertNotEqual(canon_traces(payload("/hello")), canon_traces({}))

    def test_stable_sdk_metadata_is_not_normalized_away(self):
        self.assertNotEqual(canon_traces(payload("/hello")), canon_traces(payload("/hello", "different-sdk")))

    def test_export_batch_boundaries_do_not_change_instrument_contracts(self):
        def metric(points):
            return {"resourceMetrics": [{"scopeMetrics": [{"scope": {"name": "sdk"}, "metrics": [{
                "name": "memory", "unit": "By", "gauge": {"dataPoints": [
                    {"attributes": [{"key": "type", "value": {"stringValue": value}}]} for value in points
                ]},
            }]}]}]}
        combined = metric(["heap", "stack"])
        separated = {"resourceMetrics": metric(["heap"])["resourceMetrics"] + metric(["stack"])["resourceMetrics"]}
        self.assertEqual(canon_metrics(combined), canon_metrics(separated))
        self.assertNotEqual(canon_metrics(combined), canon_metrics(metric(["heap"])))


if __name__ == "__main__":
    unittest.main()
