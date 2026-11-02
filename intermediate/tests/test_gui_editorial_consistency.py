"""Protect the chapter 21/23 GUI validation boundary and edited exercises."""
from pathlib import Path
import unittest

TEX = Path(__file__).resolve().parents[1] / "Intermediate_Textbook.tex"


class GuiEditorialConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TEX.read_text(encoding="utf-8")

    def test_obsolete_gui_claims_removed(self):
        for obsolete in (
            "GUIはまだ統合していません。",
            "画面上で実際にクリックできるかも、まだGUI統合が必要です。",
            "GUI実機操作はまだ完成していません。",
        ):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, self.text)

    def test_bounded_x11_claim_and_unverified_environments(self):
        for expected in (
            "Linux X11仮想デスクトップで確認した有限の操作例",
            "物理GPU・他OSでの表示は未検証",
            "スクリーンリーダーへの通知も未実装",
            "配布PDF・ZIPとの",
            "10×10 GUIのOS上での有限操作",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_exercises_end_in_observable_actions(self):
        for expected in (
            "16要素になるか短いBendコードで確かめてみましょう。",
            "照合してみましょう。",
            "順序を図にして説明してみましょう。",
            "対応する返り値を表に整理してみましょう。",
            "隣接位置三か所を図に描き、実行結果と照合してみましょう。",
            "\\code{--verdict}の結果と照合してみましょう。",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)


    def test_current_reader_distribution_status(self):
        root = TEX.parent
        readme = (root / "README.md").read_text(encoding="utf-8")
        coverage = (root / "COVERAGE.md").read_text(encoding="utf-8")
        checklist = (root / "EDITORIAL_CHECKLIST.md").read_text(encoding="utf-8")
        current_coverage = coverage.partition("---")[0]
        self.assertIn("129ページPDF", current_coverage)
        self.assertIn("103エントリ", current_coverage)
        self.assertIn("原子的な名前置換", current_coverage)
        self.assertNotIn("検収をまだ終えていません", current_coverage)
        self.assertIn("現行の読者ZIPに収録しています", readme)
        self.assertIn("PDF・ZIPへの反映と配布版のX11有限検収を完了", readme)
        self.assertNotIn("次版へ収録する候補", readme)
        self.assertNotIn("合計103エントリを予定", readme)
        self.assertIn("fsyncなし", checklist)
        self.assertIn("同一UID競合", checklist)

if __name__ == "__main__":
    unittest.main()
