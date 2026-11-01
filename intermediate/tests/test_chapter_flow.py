"""Structural regression for the 23-chapter intermediate Bend textbook.

This checks presence, not pedagogical quality or actual execution. Each chapter
still needs human editorial review and its examples need independent runtime CI.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "Intermediate_Textbook.tex"
CHAPTER = re.compile(r"^\\chapter\{([^}\n]+)\}", re.MULTILINE)


def chapter_blocks(source: str) -> list[tuple[str, str]]:
    headers = list(CHAPTER.finditer(source))
    return [
        (match.group(1), source[match.end():headers[i + 1].start() if i + 1 < len(headers) else len(source)])
        for i, match in enumerate(headers)
    ]


class ChapterFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chapters = chapter_blocks(TEX.read_text(encoding="utf-8"))

    def test_exactly_23_chapters(self):
        self.assertEqual(len(self.chapters), 23)

    def test_every_chapter_has_goal_code_and_exercise(self):
        for number, (title, body) in enumerate(self.chapters, 1):
            with self.subTest(chapter=number, title=title):
                self.assertIn(r"\sectiongoal{", body)
                self.assertIn(r"\begin{lstlisting}", body)
                self.assertIn(r"\exercise{", body)

    def test_file_and_clock_lessons_are_not_lost(self):
        self.assertIn("File.read_bytes", self.chapters[6][1])
        self.assertIn("45_binary_file.bend", self.chapters[6][1])
        self.assertIn("IO.now", self.chapters[7][1])
        self.assertIn("IO.sleep", self.chapters[7][1])
        self.assertIn("46_elapsed_clock.bend", self.chapters[7][1])

    def test_file_and_clock_verified_lesson_sections(self):
        chapter7, chapter8 = self.chapters[6][1], self.chapters[7][1]
        self.assertIn("54_binary_chunks.bend", chapter7)
        self.assertIn("55_clock_intervals.bend", chapter8)
        self.assertIn("4回目の空リスト", chapter7)
        self.assertIn("3回実行", chapter8)
        for number, chapter in ((7, chapter7), (8, chapter8)):
            with self.subTest(chapter=number):
                self.assertIn("有限", chapter)
                self.assertIn(r"\exercise{", chapter)

    def test_chapter21_gui_save_explains_verified_boundary(self):
        chapter = self.chapters[20][1]
        for phrase in ("nxn_gui_app_store.bend", "nxn_gui_history.bend",
                       "nxn_gui_store.bend", "BEND2-GUI-1|20261029|0|199|END",
                       "原子的な保存ではありません", "X11仮想デスクトップ"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, chapter)
        self.assertIn(r"\exercise{", chapter)

    def test_chapter18_gui_claim_matches_verified_platform_scope(self):
        chapter = self.chapters[17][1]
        for phrase in ("Linux X11仮想デスクトップ", "S/Lキー", "物理GPU",
                       "他OS", "原子的な更新", "有限"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, chapter)
        self.assertNotIn("実際のマウス操作は未検証です", chapter)
        self.assertNotIn("完成したGUIの検証はまだ済んでいません", chapter)
        self.assertNotIn("追加されましたが、0の連鎖公開についても", chapter)
        for phrase in ("保存失敗は赤い32×32画素の四角3個",
                       "失敗時にも盤面を維持", "Linux X11仮想デスクトップ",
                       "物理GPU・他OSでの表示は未検証",
                       "スクリーンリーダーへの通知", "原子的な名前置換はLinux限定の検証候補",
                       "有限検証済みの保存失敗通知（赤い四角3個）"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, chapter)
        self.assertNotIn("保存失敗の画面通知、ファイルの原子的な更新は未検証・未実装", chapter)
        self.assertNotIn("物理GPU・他OS・保存失敗表示などの未確認項目", chapter)

    def test_chapter21_status_gui_is_taught_with_scope(self):
        chapter = self.chapters[20][1]
        for phrase in ("nxn_gui_status_app.bend", "nxn_gui_feedback_store.bend",
                       "保存成功", "読込成功", "保存失敗", "読込失敗",
                       "緑1個", "青2個", "赤3個", "橙4個",
                       "32画素四方", "U32.is_ge(notice, 4)",
                       "スクリーンリーダー", "原子的な保存",
                       "X11仮想デスクトップ"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, chapter)
        self.assertIn(r"\exercise{", chapter)

    def test_gui_status_reader_text_matches_bend_shape_implementation(self):
        chapter = self.chapters[20][1]
        self.assertNotIn(r"通知は\textbf{色だけ}", chapter)
        self.assertNotIn("色だけではない通知", chapter)
        self.assertIn("この旧保存対応GUIには", chapter)
        self.assertIn("次節で、色と四角の個数を使う通知付きGUI", chapter)
        self.assertNotIn(r"ただし\textbf{失敗を画面に通知する機能は未実装}", chapter)
        gui = (ROOT / "minesweeper" / "nxn_gui_status_app.bend").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for threshold in (2, 3, 4):
            self.assertIn(f"paint_if(U32.is_ge(notice, {threshold})", gui)
        for phrase in ("緑1個", "青2個", "赤3個", "橙4個", "スクリーンリーダー"):
            self.assertIn(phrase, readme)
        self.assertNotIn("これは色だけの通知", readme)
        self.assertNotIn("失敗の画面通知、原子的", readme)
        self.assertIn("nxn_gui_atomic_store.bend", readme)
        self.assertIn("Atomic.save_atomic_report(model)", gui)

    def test_chapter19_two_cell_lesson_is_runnable(self):
        chapter = self.chapters[18][1]
        for phrase in ("56_atomic_two_cells.bend", "Array.atomic.add(array, 1, 7)",
                       "順次実行の観測", "物理GPU", "二回目の更新先を1番から0番"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, chapter)
        self.assertIn(r"\sample{56_atomic_two_cells.bend}", chapter)
        self.assertIn(r"\exercise{", chapter)

    def test_reader_samples_match_bend_verified_fixtures(self):
        for name, fixture in (
            ("54_binary_chunks.bend", "binary_chunks.bend"),
            ("55_clock_intervals.bend", "clock_intervals.bend"),
            ("56_atomic_two_cells.bend", "atomic_two_cells.bend"),
        ):
            with self.subTest(sample=name):
                self.assertEqual(
                    (ROOT / "src" / name).read_bytes(),
                    (ROOT / "scripts" / "fixtures" / fixture).read_bytes(),
                )

    def test_chapter_parser_ignores_sections(self):
        fixture = "\\part{X}\n\\chapter{A}\n\\section{a}\ntext\n\\chapter{B}\n\\exercise{b}"
        self.assertEqual(chapter_blocks(fixture), [("A", "\n\\section{a}\ntext\n"), ("B", "\n\\exercise{b}")])


if __name__ == "__main__":
    unittest.main()
