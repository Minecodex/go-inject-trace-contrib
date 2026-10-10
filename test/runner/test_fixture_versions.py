import unittest

from fixture_modules import declared_modules, pin_declared_modules


class FixtureVersionTests(unittest.TestCase):
    def test_declared_framework_cannot_be_upgraded_by_the_reference_tool(self):
        original = """module fixture
go 1.25
require (
    github.com/openai/openai-go/v3 v3.53.0
    github.com/kakj-go/go-inject-trace-contrib v0.0.0
)
replace github.com/kakj-go/go-inject-trace-contrib => /contrib
"""
        frozen = pin_declared_modules(original)
        self.assertIn("github.com/openai/openai-go/v3 => github.com/openai/openai-go/v3 v3.53.0", frozen)
        self.assertEqual(frozen.count("github.com/kakj-go/go-inject-trace-contrib =>"), 1)

    def test_single_line_requirement_is_frozen(self):
        frozen = pin_declared_modules("module fixture\ngo 1.25\nrequire example.com/sdk v1.2.3\n")
        self.assertIn("example.com/sdk => example.com/sdk v1.2.3", frozen)

    def test_sdk_major_module_is_not_its_parent_module(self):
        modules = declared_modules("require github.com/openai/openai-go/v3 v3.53.0\n")
        self.assertIn("github.com/openai/openai-go/v3", modules)
        self.assertNotIn("github.com/openai/openai-go", modules)


if __name__ == "__main__":
    unittest.main()
