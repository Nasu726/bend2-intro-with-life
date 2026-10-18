"""Structural tests for the intermediate textbook.

These tests check that the draft does not advertise material absent from Git.
They do not certify game completion or GUI execution.
"""
from pathlib import Path
import hashlib
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

    def test_adopted_cover_is_unchanged(self):
        # The reader-approved C cover is immutable unless explicitly revised.
        cover = ROOT / "cover_art.tex"
        raw = cover.read_bytes()
        header = f"blob {len(raw)}".encode("ascii") + bytes([0])
        git_blob_sha = hashlib.sha1(header + raw).hexdigest()
        self.assertEqual(git_blob_sha, "ba9b5c4cb296e3adfd119ace6b55abc419c6faf1")
        self.assertIn(
            chr(92) + "input{intermediate/cover_art.tex}",
            BOOK.read_text(encoding="utf-8"),
        )

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

    def test_pair_exists_lesson_has_real_source(self):
        text = BOOK.read_text(encoding="utf-8")
        self.assertEqual(text.count(r"\sample{52_pair_exists.bend}"), 1)
        self.assertIn(r"\code{Exists}", text)
        source = (SRC / "52_pair_exists.bend").read_text(encoding="utf-8")
        self.assertIn("def next_is_three()", source)
        self.assertIn("Exists(Nat,", source)
        self.assertIn("Tuple{2n, {==}}", source)

    def test_coverage_present(self):
        ledger = (ROOT / "COVERAGE.md").read_text(encoding="utf-8")
        for family in ("Map", "Set", "List", "Array", "IO", "File",
                       "TCP", "UDP", "Audio", "App", "law", "GPU"):
            self.assertIn(family, ledger)

    def test_gui_lesson_matches_existing_engine(self):
        text = BOOK.read_text(encoding="utf-8")
        gui = (ROOT / "minesweeper" / "gui.bend").read_text(encoding="utf-8")
        self.assertIn(r"\section{4×4 GUIでは、一マスは64画素になる}", text)
        self.assertIn(r"\code{Array.clone}", text)
        self.assertIn("bend examples/minesweeper/gui.bend --check-only", text)
        self.assertNotIn("実機のGUIは、まだ完成していません", text)
        for part in ("App.run(~Start.Stage", "Array.clone(Game.Square, cells)",
                     "U32.div(y, 64)", "Key{114, True{}}"):
            self.assertIn(part, gui)

    def test_gui_coordinate_reference_boundaries(self):
        # Independent arithmetic oracle for the chapter's 4x4 / 64px mapping.
        # This does not replace Bend's 13 executable gui_smoke checks.
        cases = (
            (0, 0, 0), (63, 63, 0), (64, 63, 1),
            (0, 64, 4), (127, 127, 5), (128, 128, 10),
            (255, 255, 15), (256, 0, None), (0, 256, None),
        )
        for x, y, expected in cases:
            actual = (y // 64) * 4 + x // 64 if x < 256 and y < 256 else None
            self.assertEqual(actual, expected, (x, y))
        gui = (ROOT / "minesweeper" / "gui.bend").read_text(encoding="utf-8")
        for term in ("U32.div(y, 64)", "U32.div(x, 64)",
                     "U32.is_lt(x, 256)", "U32.is_lt(y, 256)",
                     "U32.is_eq(button, 0)", "U32.is_eq(button, 1)"):
            self.assertIn(term, gui)

    def test_timeout_lesson_distinguishes_three_outcomes(self):
        text = BOOK.read_text(encoding="utf-8")
        source = (SRC / "29_io_within.bend").read_text(encoding="utf-8")
        for phrase in (
            r"\section{時間制限は仕事の中止ではない}",
            r"\section{Pollは「いま待つ必要がある」を表す}",
            r"\code{Ready{Some{v}}}",
            r"\code{Ready{None{}}}",
            r"\code{Wait{Unit{}}}",
            r"\code{Chan.try_send}",
            r"\code{Chan.try_recv}",
        ):
            self.assertTrue(phrase in text, f"Chapter 9 missing: {phrase}")
        self.assertIn("IO.within(U32, 1000, IO.pure(U32, 7))", source)
        self.assertIn('IO.print("Timed out")', source)

    def test_draft_status_is_honest(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("未完成", readme)
        self.assertIn("形式的証明", readme)

if __name__ == "__main__":
    unittest.main()
