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

    def test_chapter_parser_ignores_sections(self):
        fixture = "\\part{X}\n\\chapter{A}\n\\section{a}\ntext\n\\chapter{B}\n\\exercise{b}"
        self.assertEqual(chapter_blocks(fixture), [("A", "\n\\section{a}\ntext\n"), ("B", "\n\\exercise{b}")])


if __name__ == "__main__":
    unittest.main()
