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

    def test_nxn_lesson_imports_are_in_reader_bundle(self):
        """Every relative Bend import in a shipped game must also be shipped."""
        import re
        included = set(INTERMEDIATE_GAME_FILES)
        self.assertIn("nxn_playthrough.bend", included)
        self.assertIn("nxn_public_three_bridge.bend", included)
        for name in sorted(included):
            source = (ROOT / "intermediate/minesweeper" / name).read_text(
                encoding="utf-8")
            imports = set(re.findall(
                r"(?m)^import \./([A-Za-z0-9_]+\.bend)\s+as\b", source))
            self.assertFalse(imports - included,
                             f"{name} imports omitted learner files: "
                             f"{sorted(imports - included)}")

    def test_poll_example_is_learner_material(self):
        self.assertIn("53_chan_poll.bend", INTERMEDIATE_EXAMPLES)
        with zipfile.ZipFile(ROOT / "reader-packages/bend2-intermediate-reader-preview.zip") as z:
            name = "bend2-intermediate-reader/examples/53_chan_poll.bend"
            self.assertEqual(z.read(name),
                             (ROOT / "intermediate/src/53_chan_poll.bend").read_bytes())

    def test_pair_exists_sample_when_bend_is_installed(self):
        # The staging job installs Bend before invoking these bundle tests.
        # Keep local ZIP inspection usable on machines without the compiler.
        import os
        import shutil
        import subprocess
        if shutil.which("bend") is None:
            self.skipTest("Bend executable not installed")
        sample = ROOT / "intermediate" / "src" / "52_pair_exists.bend"
        env = dict(os.environ, BEND_NO_TELEMETRY="1")
        for args in (["bend", str(sample), "--check-only"], ["bend", str(sample)]):
            result = subprocess.run(args, capture_output=True, text=True,
                                    timeout=180, env=env, cwd=ROOT)
            self.assertEqual(result.returncode, 0,
                             f"{args} failed:\\n{result.stdout}\\n{result.stderr}")
            if len(args) == 2:
                self.assertEqual(result.stdout.strip(), "5")

    def test_intro_bundle(self):
        self.check_one("intro")

    @unittest.skipUnless((ROOT / "intermediate/Bend2を使いこなす_プレビュー.pdf").exists(),
                         "Intermediate manuscript is on its separate PR branch")
    def test_intermediate_bundle(self):
        self.check_one("intermediate")

if __name__ == "__main__":
    unittest.main()
