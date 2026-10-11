import importlib.util
from pathlib import Path
import unittest
import yaml

from port_scenarios import MULTI_APP

spec = importlib.util.spec_from_file_location(
    "triple_metadata", Path(__file__).parents[1] / "scenarios/dubbo/api/normalize_metadata.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TripleMetadataTests(unittest.TestCase):
    def test_scenario_regeneration_keeps_the_same_declared_build_contract(self):
        plugin = Path(__file__).parents[1] / "scenarios/dubbo/plugin.yml"
        config = yaml.safe_load(plugin.read_text(encoding="utf-8"))
        self.assertEqual(config["build_steps"], MULTI_APP["dubbo"]["build_steps"])
    def test_generated_handler_retains_wire_metadata_and_all_attachment_keys(self):
        source = "\tmd, _ := metadata.FromIncomingContext(ctx)\n\tfor k, v := range md {\n\t\tinvAttachment[k] = v\n\t}\n"
        adapted, count = module.normalize_metadata(source)
        self.assertEqual(count, 1)
        self.assertIn("metadata.FromIncomingContext(ctx)", adapted)
        self.assertIn("for k, v := range md", adapted)
        self.assertIn("if len(v) == 1", adapted)
        self.assertIn("invAttachment[k] = v[0]", adapted)
        self.assertIn("} else {\n\t\t\tinvAttachment[k] = v", adapted)
        self.assertNotIn("sw8", adapted)

    def test_generator_drift_is_detectable(self):
        self.assertEqual(module.normalize_metadata("unknown generated code")[1], 0)


if __name__ == "__main__":
    unittest.main()
