import tempfile
import unittest
from pathlib import Path

from run_ab import expected_file


class ExpectedFixtureTests(unittest.TestCase):
    def test_the_declared_framework_fixture_is_used_and_missing_variants_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "excepted.yml").write_text("default")
            (root / "config").mkdir()
            (root / "config/version.yml").write_text("version-specific")
            self.assertEqual(expected_file(root), "excepted.yml")
            self.assertEqual(expected_file(root, "config/version.yml"), "config/version.yml")
            with self.assertRaises(ValueError):
                expected_file(root, "config/missing.yml")
            with self.assertRaises(ValueError):
                expected_file(root, "../excepted.yml")


if __name__ == "__main__":
    unittest.main()
