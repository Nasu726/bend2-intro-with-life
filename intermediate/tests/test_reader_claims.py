"""Regression guard for the reader-facing preview description.

This checks only documentation claims against the ZIP builder's allowlist.
It does not replace Bend execution, TeX compilation, or ZIP byte inspection.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from build_reader_bundle import INTERMEDIATE_EXAMPLES, INTERMEDIATE_GAME_FILES


class ReaderClaims(unittest.TestCase):
    def test_readme_counts_and_compiler_compatibility(self):
        readme = (ROOT / "intermediate/README.md").read_text(encoding="utf8")
        self.assertIn(f"通常サンプル{len(INTERMEDIATE_EXAMPLES)}本", readme)
        self.assertIn(f"ゲーム実習{len(INTERMEDIATE_GAME_FILES)}本", readme)
        self.assertIn("Bend 2.0.37", readme)
        self.assertIn("Bend 2.0.38", readme)


if __name__ == "__main__":
    unittest.main()
