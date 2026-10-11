import unittest

from control_contracts import gateway_contract


class ControlContractTests(unittest.TestCase):
    def test_gateway_does_not_remove_business_or_unrelated_failure_logs(self):
        text = "rpc error: code = Unimplemented desc = Method not found: skywalking.v3.ProfileTask/getProfileTaskCommands"
        control = {"endpoint": "", "body": {"content": {"text": text}}, "traceContext": {"traceId": "N/A", "traceSegmentId": "N/A", "spanId": -1}}
        business = {**control, "endpoint": "GET:/business"}
        unrelated = {**control, "body": {"content": {"text": "database unavailable"}}}
        original = {"logItems": [{"logSize": "ge 3", "logs": [control, business, unrelated]}]}
        derived, removed = gateway_contract(original)
        self.assertEqual(removed, 1)
        self.assertEqual(derived["logItems"][0]["logs"], [business, unrelated])
        self.assertEqual(original["logItems"][0]["logs"], [control, business, unrelated])


if __name__ == "__main__":
    unittest.main()
