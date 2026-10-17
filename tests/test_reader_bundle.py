"""Verify that ZIPs contain exactly the learner files and no reference solutions."""
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_reader_bundle import (INTRO_EXAMPLES, INTERMEDIATE_EXAMPLES,
                                 INTERMEDIATE_GAME_FILES, readme, build)

class TestReaderBundle(unittest.TestCase):
    def check_one(self, kind):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p = build(kind, Path(tmp))
            prefix = "bend2-" + kind + "-reader/"
            expected_examples = INTRO_EXAMPLES if kind == "intro" else INTERMEDIATE_EXAMPLES
            expected = {prefix + n for n in ("README.md", "LICENSE", "textbook.pdf")}
            expected |= {prefix + "examples/" + name for name in expected_examples}
            if kind == "intermediate":
                expected |= {prefix + "examples/minesweeper/" + name
                             for name in INTERMEDIATE_GAME_FILES}
            with zipfile.ZipFile(p) as z:
                names = z.namelist()
                self.assertEqual(set(names), expected)
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(z.testzip() is None)
                self.assertIn(b"%PDF", z.read(prefix + "textbook.pdf")[:16])
                self.assertIn("Bend 2", z.read(prefix + "README.md").decode("utf8"))
                for name in names:
                    self.assertNotIn("solutions", name.lower())
                    self.assertNotIn("EDITORIAL", name)
                    self.assertNotIn("COVERAGE", name)
                    self.assertNotIn(".github", name)
                    self.assertFalse(name.endswith(".tex"))
                    self.assertFalse(name.endswith(".py"))

    def test_intro_bundle(self):
        self.check_one("intro")

    @unittest.skipUnless((ROOT / "intermediate/Bend2を使いこなす_プレビュー.pdf").exists(),
                         "Intermediate manuscript is on its separate PR branch")
    def test_intermediate_bundle(self):
        self.check_one("intermediate")

if __name__ == "__main__":
    unittest.main()
