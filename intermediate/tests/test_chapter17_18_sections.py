"""Static review of chapters 17 and 18; not a Bend proof or GUI acceptance test."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^\\chapter\{[^}\n]+\}", re.MULTILINE)
SECTION = re.compile(r"^\\section\{([^}\n]+)\}", re.MULTILINE)
SAMPLE = re.compile(r"\\sample\{([^}]+)\}")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def sections(number: int) -> list[tuple[str, str]]:
    tex = read("Intermediate_Textbook.tex")
    chapters = list(CHAPTER.finditer(tex))
    if len(chapters) != 23:
        raise AssertionError(f"Expected 23 chapters, found {len(chapters)}")
    start = chapters[number - 1].end()
    end = chapters[number].start() if number < len(chapters) else len(tex)
    body = tex[start:end]
    matches = list(SECTION.finditer(body))
    return [(m.group(1), body[m.end():matches[i + 1].start()
                              if i + 1 < len(matches) else len(body)])
            for i, m in enumerate(matches)]


class BoardInvariantAndTrustReview(unittest.TestCase):
    def test_chapter17_five_sections_and_single_sample(self):
        expected = [
            ("旗を立てたら地雷が移動する？", []),
            ("まず二つの数値だけで試す", ["34_mine_mask_law.bend"]),
            ("16マスの配列へ広げる", []),
            ("表示済みの数字は閉じてよい？", []),
            ("数字の正しさは別の条件になる", []),
        ]
        self.assertEqual([(h, SAMPLE.findall(b)) for h, b in sections(17)], expected)

    def test_chapter18_five_sections_and_inline_example(self):
        expected = [
            "動いたからといって、全部正しい？",
            "実行結果と法則の証明を比べる",
            "正しい法則でも、問いが足りない場合",
            "実機でしか分からないこと",
            "小さな確認から確かな説明へ",
        ]
        chapter = sections(18)
        self.assertEqual([h for h, _ in chapter], expected)
        self.assertEqual([SAMPLE.findall(b) for _, b in chapter], [[]] * 5)
        self.assertIn("24_bool_proofs.bend", chapter[1][1])
        self.assertTrue((ROOT / "src/24_bool_proofs.bend").is_file())

    def test_two_laws_are_distinct_from_one_runtime_example(self):
        code = read("src/34_mine_mask_law.bend")
        for phrase in (
            "type MiniBoard is Data:",
            "MiniBoard{mines: U32, flags: U32}",
            "MiniBoard{mines, U32.xor(flags, 1)}",
            "law toggle_keeps_mines:",
            "law toggle_changes_flag:",
            "for mines: U32",
            "for flags: U32",
            "def toggle_keeps_mines(mines, flags):",
            "def toggle_changes_flag(mines, flags):",
            "flags_of(toggle_first(MiniBoard{5, 0}))",
        ):
            self.assertIn(phrase, code)
        self.assertIn('"34_mine_mask_law.bend": "1"', read("scripts/test_examples.py"))
        self.assertIn("出力は\\code{1}", dict(sections(17))["まず二つの数値だけで試す"])

    def test_existing_runner_checks_proofs_separately(self):
        runner = read("scripts/test_examples.py")
        for phrase in (
            'SAMPLES / "34_mine_mask_law.bend"',
            'SAMPLES / "24_bool_proofs.bend"',
            '"--verdict"',
            '"ALL PROOFS CHECK"',
        ):
            self.assertIn(phrase, runner)
        self.assertIn('"24_bool_proofs.bend": "1"', runner)
        self.assertIn("law not_twice:", read("src/24_bool_proofs.bend"))
        self.assertIn("for b: Bool", read("src/24_bool_proofs.bend"))

    def test_u32_law_does_not_imply_legal_4x4_mask(self):
        body = dict(sections(17))["16マスの配列へ広げる"]
        for phrase in ("board4_toggle_keeps_all_mines", "LAWS.bend", "PROOF.bend",
                       "32ビット", "16マス", "別の条件"):
            self.assertIn(phrase, body)

    def test_open_monotonicity_has_reset_exception(self):
        body = dict(sections(17))["表示済みの数字は閉じてよい？"]
        for phrase in (r"\operatorname{open}", r"\subseteq",
                       r"\operatorname{reveal}", "単調性", "リセット"):
            self.assertIn(phrase, body)
        self.assertNotIn("law ", body)

    def test_correct_clues_are_a_separate_requirement(self):
        body = dict(sections(17))["数字の正しさは別の条件になる"]
        for phrase in ("10_board_neighbors.bend", "数字を2", "地雷マスク",
                       "独立した法則"):
            self.assertIn(phrase, body)
        self.assertTrue((ROOT / "src/10_board_neighbors.bend").is_file())

    def test_runtime_and_proof_are_not_game_wide_claims(self):
        body = dict(sections(18))["実行結果と法則の証明を比べる"]
        for phrase in ("law not_twice:", "for b: Bool", "--verdict",
                       r"\code{1}", "ゲーム全体"):
            self.assertIn(phrase, body)
        self.assertIn("何もしない関数",
                      dict(sections(18))["正しい法則でも、問いが足りない場合"])

    def test_gui_evidence_and_unverified_environments_are_separate(self):
        body = dict(sections(18))["実機でしか分からないこと"]
        for phrase in ("10×10", "Linux X11", "有限", "32×32", "赤",
                       "原子的", "名前置換", "電源断", "同時実行",
                       "物理GPU", "他OS", "スクリーンリーダー"):
            self.assertIn(phrase, body)

    def test_exercises_and_audit_limits_are_explicit(self):
        ch17 = "\n".join(b for _, b in sections(17))
        ch18 = "\n".join(b for _, b in sections(18))
        self.assertEqual(ch17.count(r"\exercise{"), 1)
        self.assertEqual(ch18.count(r"\exercise{"), 1)
        self.assertIn("説明しましょう", ch17)
        self.assertIn("書いてみましょう", ch18)
        summary = dict(sections(18))["小さな確認から確かな説明へ"]
        self.assertIn("全256座標対", summary)
        self.assertIn("全操作列の証明にはなりません", summary)


if __name__ == "__main__":
    unittest.main()
