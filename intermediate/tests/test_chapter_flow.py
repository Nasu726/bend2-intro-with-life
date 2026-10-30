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

    def test_reader_samples_match_bend_verified_fixtures(self):
        for name, fixture in (
            ("54_binary_chunks.bend", "binary_chunks.bend"),
            ("55_clock_intervals.bend", "clock_intervals.bend"),
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
