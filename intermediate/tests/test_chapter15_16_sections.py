"""Static section-by-section review of chapters 15 and 16.

These checks are not a substitute for the real Bend/Lean verdict, execution,
PDF rendering, or an audit of whether the laws fully specify the game.
"""
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
    headings = list(SECTION.finditer(body))
    return [(m.group(1), body[m.end():headings[i + 1].start()
                              if i + 1 < len(headings) else len(body)])
            for i, m in enumerate(headings)]


class ProofSectionReview(unittest.TestCase):
    def test_chapter15_four_sections_and_real_sample(self):
        expected = [
            ("「旗を二回押せば戻る」だけで十分？", []),
            ("小さなlawを書いて確かめる", ["04_flag_laws.bend"]),
            ("正しいのに、仕様が足りないことがある", []),
            ("大きなプログラムではファイルを分ける", []),
        ]
        self.assertEqual([(h, SAMPLE.findall(b)) for h, b in sections(15)], expected)
        self.assertTrue((ROOT / "src/04_flag_laws.bend").is_file())

    def test_chapter16_four_sections_and_real_samples(self):
        expected = [
            ("二つの値なら場合分けで確かめられる", ["24_bool_proofs.bend"]),
            ("自然数を一つずつ確かめることはできない", ["33_nat_induction.bend"]),
            ("帰納法で何を再利用しているのか", []),
            ("大きな証明では補題を使う", []),
        ]
        self.assertEqual([(h, SAMPLE.findall(b)) for h, b in sections(16)], expected)
        for name in ("24_bool_proofs.bend", "33_nat_induction.bend"):
            self.assertTrue((ROOT / "src" / name).is_file(), name)

    def test_flag_involution_is_not_a_complete_specification(self):
        code = read("src/04_flag_laws.bend")
        for phrase in ("law toggle_twice:", "law opened_stays_open:",
                       "def toggle_twice(c):", "def opened_stays_open():",
                       "case Hidden{}:", "case Marked{}:", "case Open{}:"):
            self.assertIn(phrase, code)
        self.assertNotIn("law hidden_is_marked:", code)
        ch = dict(sections(15))
        self.assertIn("何もしない関数", ch["「旗を二回押せば戻る」だけで十分？"])
        self.assertIn("二つだけでは", ch["正しいのに、仕様が足りないことがある"])
        self.assertIn("law hidden_is_marked:", ch["正しいのに、仕様が足りないことがある"])

    def test_chapter15_proof_not_confused_with_runtime(self):
        ch = dict(sections(15))
        proof = ch["小さなlawを書いて確かめる"]
        for phrase in ("for c: Cover", "toggle(toggle(c)) == c",
                       "ALL PROOFS CHECK", "--verdict", "Lean 4"):
            self.assertIn(phrase, proof)
        self.assertIn("LAWS.bend", ch["大きなプログラムではファイルを分ける"])
        self.assertIn("PROOF.bend", ch["大きなプログラムではファイルを分ける"])

    def test_boolean_proof_covers_both_constructors(self):
        code = read("src/24_bool_proofs.bend")
        for phrase in ("law not_twice:", "for b: Bool", "case True{}:",
                       "case False{}:", "Bool.to_u32(Bool.not(Bool.not(True{})))"):
            self.assertIn(phrase, code)
        self.assertIn("取り得る値が二つだけ",
                      dict(sections(16))["二つの値なら場合分けで確かめられる"])
        self.assertIn('"24_bool_proofs.bend": "1"', read("scripts/test_examples.py"))

    def test_nat_induction_is_universal_not_sample_testing(self):
        code = read("src/33_nat_induction.bend")
        for phrase in ("law times_zero:", "for x: Nat",
                       "Nat.mul(x, 0n) == 0n", "case 0n:", "case 1n+p:",
                       "%times_zero(p)", "def main() -> U32:\n  0"):
            self.assertIn(phrase, code)
        ch = dict(sections(16))
        self.assertIn("さらに大きい値について正しいと示したことにはなりません",
                      ch["自然数を一つずつ確かめることはできない"])
        self.assertIn("%times_zero(p)", ch["帰納法で何を再利用しているのか"])
        self.assertIn("それだけでは全自然数についての証明にはなりません",
                      ch["帰納法で何を再利用しているのか"])
        self.assertIn('"33_nat_induction.bend": "0"', read("scripts/test_examples.py"))

    def test_proof_exercise_runner_checks_acceptance_and_rejection(self):
        runner = read("scripts/test_proof_exercises.py")
        for phrase in ("def accepted(", "def rejected(", "def replace_once(",
                       "accepted(flag_verified)", "rejected(flag_mutant)",
                       "accepted(nat_changed)", "rejected(nat_unproved)",
                       'if executed != "1":', "ALL PROOFS CHECK"):
            self.assertIn(phrase, runner)
        self.assertIn(r"case Hidden{}:\n      Hidden{}", runner)
        self.assertIn("%times_zero(p)", runner)
        self.assertIn("tempfile.TemporaryDirectory()", runner)

    def test_exercises_are_not_mistaken_for_verified_reader_samples(self):
        ch15 = "\n".join(body for _, body in sections(15))
        ch16 = "\n".join(body for _, body in sections(16))
        self.assertEqual(ch15.count(r"\exercise{"), 1)
        self.assertEqual(ch16.count(r"\exercise{"), 1)
        self.assertIn("照合してみましょう", ch15)
        self.assertIn("調べてください", ch16)
        self.assertIn("なぜ小さい値についての証明が必要", ch16)
        self.assertNotIn("law hidden_is_marked:", read("src/04_flag_laws.bend"))


if __name__ == "__main__":
    unittest.main()
