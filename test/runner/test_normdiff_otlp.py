import unittest

from normdiff_otlp import apply_fixture_identity, canon_metrics, canon_traces


def payload(path, sdk_name="opentelemetry"):
    return {"resourceSpans": [{
        "resource": {"attributes": [{"key": "telemetry.sdk.name", "value": {"stringValue": sdk_name}}]},
        "scopeSpans": [{"scope": {"name": "http"}, "spans": [{
            "traceId": "trace", "spanId": "span", "name": "GET", "kind": 2,
            "attributes": [{"key": "url.path", "value": {"stringValue": path}}],
        }]}],
    }]}


class TelemetryNormalizationTests(unittest.TestCase):
    def test_only_the_actual_api_identity_may_differ_between_fresh_clusters(self):
        def kube(uid):
            data = payload("/pods")
            data["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"].append({"key": "k8s.pod.uid", "value": {"stringValue": uid}})
            return data
        uid_a = "00000000-0000-0000-0000-000000000001"
        uid_b = "00000000-0000-0000-0000-000000000002"
        reference = canon_traces(apply_fixture_identity(kube(uid_a), {"k8s.pod.uid": uid_a}))
        self.assertEqual(reference, canon_traces(apply_fixture_identity(kube(uid_b), {"k8s.pod.uid": uid_b})))
        self.assertNotEqual(reference, canon_traces(apply_fixture_identity(kube(uid_b), {"k8s.pod.uid": uid_a})))
        self.assertNotEqual(reference, canon_traces(apply_fixture_identity(payload("/pods"), {"k8s.pod.uid": uid_a})))

    def test_fixture_identity_cannot_hide_stable_sdk_attributes(self):
        with self.assertRaises(ValueError):
            apply_fixture_identity(payload("/pods"), {"telemetry.sdk.name": "opentelemetry"})

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
