"""Checks for chapter order and accidental scope/editorial regressions."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "Bend2_Life_Textbook.tex"


class TextbookStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = TEX.read_text(encoding="utf-8")
        cls.part1_start = cls.source.index(r"\part{Bend 2の基本文法を学ぶ}")
        cls.part2_start = cls.source.index(r"\part{ライフゲームを設計して組み立てる}")
        cls.part3_start = cls.source.index(r"\part{演習の解答と実行リファレンス}")
        cls.part1 = cls.source[cls.part1_start : cls.part2_start]
        cls.part2 = cls.source[cls.part2_start : cls.part3_start]

    def test_part_one_has_no_game_rules(self):
        for term in ("B3/S23", "グライダー", "トーラス", "64要素", "8×8", "生死規則"):
            with self.subTest(term=term):
                self.assertNotIn(term, self.part1)

    def test_types_precede_functions_and_pattern_matching(self):
        types = self.part1.index(r"\chapter{値とデータ型を理解する}")
        self.assertLess(types, self.part1.index(r"\chapter{関数を定義して数値を計算する}"))
        self.assertLess(types, self.part1.index(r"\chapter{パターンマッチで場合分けをする}"))

    def test_higher_order_functions_precede_monads(self):
        self.assertLess(self.part1.index(r"\chapter{高階関数とクロージャを使う}"),
                        self.part1.index(r"\chapter{モナドと\code{do}構文を理解する}"))

    def test_part_two_starts_with_life_specification(self):
        first = self.part2.index(r"\chapter{ライフゲームのしくみと制作するもの}")
        implementation = self.part2.index(r"\chapter{座標とindex関数で8×8盤面を扱う}")
        self.assertLess(first, implementation)
        self.assertIn("B3/S23", self.part2[first:implementation])

    def test_life_uses_xy_index_consistently(self):
        self.assertIn("def index(x: U32, y: U32)", self.part2)
        for sample in ("05_glider.bend", "06_neighbors.bend",
                       "07_life_core.bend", "08_life_terminal.bend", "life_core.bend"):
            code = (ROOT / "src" / sample).read_text(encoding="utf8")
            self.assertIn("def index(x: U32, y: U32) -> U32:", code)
            self.assertIn("(y * 8 + x : U32)", code)
            self.assertIn("index(", code)
        self.assertIn("index(1, 0)", (ROOT/"src/05_glider.bend").read_text())
        self.assertIn("index(2, 2)", (ROOT/"src/05_glider.bend").read_text())

    def test_no_editorial_warnings_to_readers(self):
        for term in ("ゲームの規則とプログラミング言語の仕様は別物", "別物であることを意識", "このPartでは、まず"):
            with self.subTest(term=term):
                self.assertNotIn(term, self.source)

    def test_intro_only_sections(self):
        self.assertEqual(self.source.count(r"\chapter{"), 24)
        self.assertEqual(self.source.count(r"\part{"), 3)
        self.assertEqual(self.source.count("\\partchaptertoc\n"), 3)
        for chapter in ("ライフゲームを画面に表示する準備",):
            self.assertNotIn(r"\chapter{" + chapter, self.source)

    def test_bend_signature_features_included(self):
        for title in ("独立した計算をCPUで並列に実行する", "GPUで計算を実行する", "ライフゲームの規則を形式的に証明する"):
            with self.subTest(title=title):
                self.assertIn(r"\chapter{" + title + "}", self.part2)
        for code in ("09_parallel_tree.bend", "10_gpu_tree.bend", "11_rule_proofs.bend", "24_proof_induction.bend", "31_parallel_life_pair.bend", "32_gpu_life_call.bend"):
            self.assertTrue((ROOT / "src" / code).exists())

    def test_importable_life_core_matches_chapter_sample(self):
        self.assertEqual((ROOT / "src" / "life_core.bend").read_bytes(),
                         (ROOT / "src" / "07_life_core.bend").read_bytes())

    def test_example_paths_exist(self):
        for basename in re.findall(r"\\readcode\{([^}]+)\}", self.source):
            with self.subTest(basename=basename):
                self.assertTrue((ROOT / "src" / basename).exists(), basename)


if __name__ == "__main__":
    unittest.main()
