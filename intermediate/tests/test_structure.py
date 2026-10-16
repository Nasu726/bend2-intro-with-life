"""Structural tests for the intermediate textbook.

These tests check that the draft does not advertise material absent from Git.
They do not certify game completion or GUI execution.
"""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from build_reader_bundle import INTERMEDIATE_EXAMPLES

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "Intermediate_Textbook.tex"
SRC = ROOT / "src"

class BookStructure(unittest.TestCase):
    def test_book_present(self):
        self.assertTrue(BOOK.exists())
        self.assertGreater(BOOK.stat().st_size, 10000)

    def test_sections(self):
        text = BOOK.read_text(encoding="utf-8")
        self.assertEqual(text.count(r"\part{"), 6)
        self.assertGreaterEqual(text.count(r"\chapter{"), 20)
        for heading in ("Baseを調べる", "MapとSet", "Fileとリソース",
                        "Appとイベント", "lawを先に書く", "運ゲー無し"):
            self.assertIn(heading, text)

    def test_code_listings_exist(self):
        text = BOOK.read_text(encoding="utf-8")
        samples = re.findall(r"\\sample\{([^}]+)\}", text)
        self.assertGreaterEqual(len(samples), 8)
        missing = [s for s in samples if not (SRC / s).is_file()]
        self.assertFalse(missing, f"Missing Bend files: {missing}")
        self.assertEqual(len(samples), len(set(samples)), "Duplicate full source listings waste reader pages")
        self.assertEqual(set(samples), set(INTERMEDIATE_EXAMPLES),
                         "Every bundled exercise must be introduced once in the textbook")

    def test_coverage_present(self):
        ledger = (ROOT / "COVERAGE.md").read_text(encoding="utf-8")
        for family in ("Map", "Set", "List", "Array", "IO", "File",
                       "TCP", "UDP", "Audio", "App", "law", "GPU"):
            self.assertIn(family, ledger)

    def test_draft_status_is_honest(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("未完成", readme)
        self.assertIn("形式的証明", readme)

if __name__ == "__main__":
    unittest.main()
