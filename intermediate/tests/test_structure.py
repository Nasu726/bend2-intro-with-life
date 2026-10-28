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

    def test_binary_file_and_elapsed_clock_lessons(self):
        text = BOOK.read_text(encoding="utf-8")
        binary = (SRC / "45_binary_file.bend").read_text(encoding="utf-8")
        clock = (SRC / "46_elapsed_clock.bend").read_text(encoding="utf-8")
        self.assertEqual(text.count(r"\sample{45_binary_file.bend}"), 1)
        self.assertEqual(text.count(r"\sample{46_elapsed_clock.bend}"), 1)
        self.assertIn("File.write_bytes(file, [0, 10, 13, 255])", binary)
        self.assertIn("File.read_bytes(input, 16)", binary)
        self.assertIn("IO.now()", clock)
        self.assertIn("IO.sleep(20)", clock)
        self.assertIn("00 0A 0D FF", text)
        self.assertIn(r"\code{Nat.sub}", text)
        self.assertIn(r"\section{古い保存を上書きし、失敗も確かめる}", text)
        self.assertIn("old-save", text)
        self.assertIn("sample_bytes.bin').read_bytes().hex(' ')", text)
        self.assertIn("この\code{21}は表示形式を示す一例", text)

    def test_each_chapter_has_a_goal_and_an_exercise(self):
        text = BOOK.read_text(encoding="utf-8")
        chapters = re.split(r"\\chapter\{[^}]+\}", text)[1:]
        self.assertEqual(len(chapters), 23, "The book must retain its 23 chapters")
        for number, chapter in enumerate(chapters, 1):
            with self.subTest(chapter=number):
                self.assertEqual(chapter.count(r"\sectiongoal{"), 1)
                self.assertGreaterEqual(chapter.count(r"\exercise{"), 1)

    def test_code_listings_exist(self):
        text = BOOK.read_text(encoding="utf-8")
        samples = re.findall(r"\\sample\{([^}]+)\}", text)
        self.assertGreaterEqual(len(samples), 8)
        missing = [s for s in samples if not (SRC / s).is_file()]
        self.assertFalse(missing, f"Missing Bend files: {missing}")
        self.assertEqual(len(samples), len(set(samples)), "Duplicate full source listings waste reader pages")
        self.assertEqual(set(samples), set(INTERMEDIATE_EXAMPLES),
                         "Every bundled exercise must be introduced once in the textbook")

    def test_reader_overview_matches_bundle_and_io_lessons(self):
        from build_reader_bundle import INTERMEDIATE_GAME_FILES
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"通常サンプル{len(INTERMEDIATE_EXAMPLES)}本", readme)
        self.assertIn(f"ゲーム実習{len(INTERMEDIATE_GAME_FILES)}本", readme)
        self.assertNotIn("**44ファイル**", readme)
        for command in ("bend examples/45_binary_file.bend",
                        "bend examples/46_elapsed_clock.bend"):
            self.assertIn(command, readme)
        self.assertIn("00 0a 0d ff", readme)
        self.assertIn("時計の値は環境によって変わり", readme)

    def test_three_clue_fixed_point_scope(self):
        from build_reader_bundle import INTERMEDIATE_GAME_FILES
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        source = (ROOT / "minesweeper" / "nxn_public_three_fixpoint.bend").read_text(encoding="utf-8")
        supplement = (ROOT / "manuscript" / "22_NxN_Bend三数字固定点.md").read_text(encoding="utf-8")
        status = (ROOT / "manuscript" / "STATUS.md").read_text(encoding="utf-8")
        plan = (ROOT / "COMPLETION_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("nxn_public_three_fixpoint.bend", readme)
        self.assertIn("期待出力は`206`", readme)
        self.assertIn("読者ZIPに収録", readme)
        self.assertIn("三公開数字に限定", readme)
        self.assertIn("def infer_three(", source)
        self.assertIn("iterate(25n", source)
        self.assertIn("三つの公開数字による単独制約の反復", supplement)
        self.assertIn("nxn_public_three_fixpoint.bend", INTERMEDIATE_GAME_FILES)
        self.assertIn("nxn_public_many_fixpoint.bend", INTERMEDIATE_GAME_FILES)
        self.assertIn("nxn_public_pair_gap.bend", INTERMEDIATE_GAME_FILES)
        self.assertIn("正本統合済み（Bend三数字固定点）", status)
        self.assertIn(f"ZIPは**{len(INTERMEDIATE_EXAMPLES)+len(INTERMEDIATE_GAME_FILES)+3}エントリ**", plan)

    def test_chapter22_variable_clues_and_pair_gap_are_in_book(self):
        from build_reader_bundle import INTERMEDIATE_GAME_FILES
        book = BOOK.read_text(encoding="utf-8")
        chapter = re.split(r"\\chapter\{[^}]+\}", book)[22]
        for name, result in (("nxn_public_many_fixpoint.bend", "6"),
                             ("nxn_public_pair_gap.bend", "203")):
            self.assertIn("bend examples/minesweeper/" + name, chapter)
            self.assertIn(name, INTERMEDIATE_GAME_FILES)
            self.assertIn(result, chapter)
        self.assertIn("type Clue is Data:", chapter)
        self.assertIn("8,631", chapter)
        self.assertIn("1,672", chapter)
        self.assertIn("48状態", chapter)
        self.assertNotIn("まだBendが自動で数字を繰り返し調べるプログラムではありません。", chapter)

    def test_pair_exists_lesson_has_real_source(self):
        text = BOOK.read_text(encoding="utf-8")
        self.assertEqual(text.count(r"\sample{52_pair_exists.bend}"), 1)
        self.assertIn(r"\code{Exists}", text)
        source = (SRC / "52_pair_exists.bend").read_text(encoding="utf-8")
        self.assertIn("def next_is_three()", source)
        self.assertIn("Exists(Nat,", source)
        self.assertIn("Tuple{2n, {==}}", source)

    def test_two_corner_lesson(self):
        text = BOOK.read_text(encoding="utf-8")
        source = (ROOT / "minesweeper" / "public_two_corners.bend").read_text(encoding="utf-8")
        self.assertIn(r"\section{公開数字を一つ増やして比べる}", text)
        self.assertIn("19506", text)
        self.assertIn("Solver.Number{0, 0}", source)
        self.assertIn("Solver.Number{15, 0}", source)

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
        for part in ("App.run(~Start.Stage", "Array.clone(Game.Square, cells)", "Board.index(",
                     "U32.div(y, 64)", "Key{114, True{}}"):
            self.assertIn(part, gui)

    def test_index_xy_contract_for_minesweeper_and_examples(self):
        board = (ROOT / "minesweeper" / "board.bend").read_text(encoding="utf8")
        gui = (ROOT / "minesweeper" / "gui.bend").read_text(encoding="utf8")
        sample = (SRC / "board_index.bend").read_text(encoding="utf8")
        demo = (SRC / "42_module_board.bend").read_text(encoding="utf8")
        for code in (board, sample):
            self.assertIn("def index(x: U32, y: U32) -> U32:", code)
            self.assertIn("(y * 4 + x : U32)", code)
        for name in ("23_cell_hit_test.bend", "32_mouse_events.bend"):
            exercise = (SRC / name).read_text(encoding="utf8")
            self.assertIn("def index(x: U32, y: U32) -> U32:", exercise)
            self.assertIn("index(U32.div(x, 32), U32.div(y, 32))", exercise)
        self.assertIn("Board.index(U32.div(x, 64), U32.div(y, 64))", gui)
        self.assertIn("Board.index(3, 2)", demo)
        for y in range(4):
            for x in range(4):
                self.assertEqual(y*4+x, 4*y+x)

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

    def test_poll_lesson_has_executable_source_and_limits(self):
        book = BOOK.read_text(encoding="utf-8")
        chapter9 = re.split(r"\\chapter\{[^}]+\}", book)[9]
        self.assertEqual(book.count(r"\sample{53_chan_poll.bend}"), 1)
        for phrase in (r"\section{空のチャネルを試して、受信待ちを見分ける}",
                       "bend examples/53_chan_poll.bend", "0\n9",
                       "Wait{Unit{}}", "Ready{Some{9}}", "閉じた後の受信を試していません"):
            self.assertIn(phrase, chapter9)
        code = (SRC / "53_chan_poll.bend").read_text(encoding="utf-8")
        self.assertIn("Chan.try_recv(U32, chan, 0)", code)
        self.assertIn("Chan.send(U32, chan, 9)", code)

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

    def test_chapters_14_18_23_have_runnable_examples(self):
        book = BOOK.read_text(encoding="utf-8")
        chapters = re.split(r"\\chapter\{[^}]+\}", book)[1:]
        checks = {
            14: ("23_cell_hit_test.bend", "bend examples/23_cell_hit_test.bend",
                 "cell_if_valid(x, y", "10"),
            18: ("24_bool_proofs.bend", "bend examples/24_bool_proofs.bend",
                 "law not_twice:", "--verdict"),
            23: ("17_list_pipeline.bend", "bend examples/17_list_pipeline.bend",
                 "List.foldl", "3n"),
        }
        for chapter_number, required in checks.items():
            chapter = chapters[chapter_number - 1]
            with self.subTest(chapter=chapter_number):
                self.assertIn(r"\begin{lstlisting}", chapter)
                for token in required:
                    self.assertIn(token, chapter)
        self.assertEqual(book.count(r"\sample{23_cell_hit_test.bend}"), 1)
        self.assertEqual(book.count(r"\sample{24_bool_proofs.bend}"), 1)
        self.assertEqual(book.count(r"\sample{17_list_pipeline.bend}"), 1)

    def test_draft_status_is_honest(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("未完成", readme)
        self.assertIn("形式的証明", readme)

if __name__ == "__main__":
    unittest.main()
