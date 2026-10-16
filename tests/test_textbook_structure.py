"""Check that the language introduction stays independent of the Life project.

This structural check complements, but does not replace, Bend compilation tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "Bend2_Life_Textbook.tex"


class TextbookStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = TEX.read_text(encoding="utf-8")
        start = cls.source.index(r"\part{Bend 2の基本文法を学ぶ}")
        end = cls.source.index(r"\part{ライフゲームを設計して組み立てる}")
        cls.part1 = cls.source[start:end]
        cls.part2 = cls.source[end:]

    def test_first_part_is_independent_of_game_rules(self):
        for phrase in ("B3/S23", "グライダー", "トーラス", "64要素",
                       "生死規則", "8×8", "ライフゲーム", "セル", "座標",
                       "近傍", "Conway", "Life", "B/S", "ゲーム", "行優先"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.part1)

    def test_basic_types_come_before_functions_and_pattern_matching(self):
        self.assertLess(self.part1.index(r'\\chapter{値とデータ型を理解する}'),
                        self.part1.index(r'\\chapter{関数を定義して数値を計算する}'))
        self.assertLess(self.part1.index(r'\\chapter{値とデータ型を理解する}'),
                        self.part1.index(r'\\chapter{パターンマッチで場合分けをする}'))

    def test_monads_precede_io(self):
        self.assertLess(self.source.index(r'\\chapter{モナドと\\code{do}構文を理解する}'),
                        self.source.index(r'\\chapter{画面出力とファイル操作を扱う}'))

    def test_second_part_starts_with_specification(self):
        spec = self.part2.index(r"\chapter{ライフゲームのしくみと制作するもの}")
        board = self.part2.index(r"\chapter{一次元配列で8×8盤面を表す}")
        self.assertLess(spec, board)
        self.assertIn("B3/S23", self.part2[spec:board])

    def test_chapters_and_part_tocs(self):
        self.assertEqual(self.source.count(r"\chapter{"), 37)
        self.assertEqual(self.source.count("\\partchaptertoc\n"), 5)
        self.assertEqual(self.source.count(r"\part{"), 5)


if __name__ == "__main__":
    unittest.main()
