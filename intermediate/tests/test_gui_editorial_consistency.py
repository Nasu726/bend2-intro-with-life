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
            "物理GPU・他OS・スクリーンリーダー通知・保存の原子的更新",
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


if __name__ == "__main__":
    unittest.main()
