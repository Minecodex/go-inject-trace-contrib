from copy import deepcopy
import unittest

from normdiff import normalize, normalize_log_body


class SkyWalkingSignalsTests(unittest.TestCase):
    def test_dubbo_logs_ignore_only_clock_process_and_metadata_listener_identity(self):
        def body(port, timestamp, pid, service="org.apache.dubbo.metadata.MetadataService", version="3.0.4"):
            return {"type": "TEXT", "content": {"text": (
                f"[DUBBO Protocol] Export service: dubbo://:{port}/{service}"
                f"?application=dubbo.io&pid={pid}&release={version}&timestamp={timestamp}&version=1.0.0"
            )}}
        original = body(34433, 100, 7)
        baseline = normalize_log_body(original)
        self.assertEqual(baseline, normalize_log_body(body(35699, 200, 9)))
        self.assertEqual(original, body(34433, 100, 7))
        self.assertNotEqual(baseline, normalize_log_body(body(35699, 200, 9, version="wrong")))
        self.assertNotEqual(baseline, normalize_log_body(body(35699, 200, 9, service="api.Greeter")))
        self.assertNotEqual(normalize_log_body(body(20000, 100, 7, service="api.Greeter")),
                            normalize_log_body(body(20001, 200, 9, service="api.Greeter")))
        self.assertNotEqual(normalize_log_body({"type": "TEXT", "content": {"text": "business timestamp=100"}}),
                            normalize_log_body({"type": "TEXT", "content": {"text": "business timestamp=200"}}))

    def test_no_context_sentinel_is_not_a_correlated_business_log(self):
        data = {"logItems": [{"logs": [{"traceContext": {"traceId": "N/A", "traceSegmentId": "N/A", "spanId": -1}}]}]}
        self.assertFalse(normalize(data)["logs"][0]["correlated"])
    def test_real_meter_names_labels_types_and_buckets_remain_required(self):
        data = {"meterItems": [{"serviceName": "fixture", "meters": [{
            "meterId": {"name": "latency", "tags": [{"name": "method", "value": "GET"}]},
            "histogramBuckets": [0, 1, 10], "histogramValues": [1, 3, 9],
        }]}]}
        baseline = normalize(data)
        sampled = deepcopy(data)
        sampled["meterItems"][0]["meters"][0]["histogramValues"] = [9, 2, 1]
        self.assertEqual(baseline, normalize(sampled))
        for field, value in (("name", "other"), ("tags", [])):
            changed = deepcopy(data)
            changed["meterItems"][0]["meters"][0]["meterId"][field] = value
            self.assertNotEqual(baseline, normalize(changed))
        changed = deepcopy(data)
        changed["meterItems"][0]["meters"][0]["histogramBuckets"] = [0, 1, 100]
        self.assertNotEqual(baseline, normalize(changed))
        self.assertNotEqual(baseline, normalize({}))

    def test_log_content_level_and_trace_correlation_remain_required(self):
        data = {"logItems": [{"serviceName": "fixture", "logs": [{
            "endpoint": "GET:/provider", "body": {"type": "TEXT", "content": {"text": "business result"}},
            "tags": {"data": [{"key": "LEVEL", "value": "info"}]}, "layer": "GENERAL",
            "traceContext": {"traceId": "a", "traceSegmentId": "b", "spanId": 0},
        }]}]}
        baseline = normalize(data)
        self.assertNotEqual(baseline, normalize({}))
        changed = deepcopy(data)
        changed["logItems"][0]["logs"][0]["body"]["content"]["text"] = "wrong result"
        self.assertNotEqual(baseline, normalize(changed))
        changed = deepcopy(data)
        changed["logItems"][0]["logs"][0]["tags"]["data"][0]["value"] = "error"
        self.assertNotEqual(baseline, normalize(changed))
        changed = deepcopy(data)
        changed["logItems"][0]["logs"][0]["traceContext"] = {}
        self.assertNotEqual(baseline, normalize(changed))


if __name__ == "__main__":
    unittest.main()
