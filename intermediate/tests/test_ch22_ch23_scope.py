"""Chapters 22-23: static scope contracts and independent finite oracles.

This is not a Bend execution, general N x N proof, or PDF verification.
"""
from collections import deque
from itertools import combinations
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def sections(number):
    parts = re.split(r"(?=^\\chapter\{)", read("Intermediate_Textbook.tex"), flags=re.M)
    chapters = [part for part in parts if part.startswith(r"\chapter{")]
    assert len(chapters) == 23
    body = chapters[number - 1]
    marks = list(re.finditer(r"^\\section\{([^}\n]+)\}", body, flags=re.M))
    return [(m.group(1), body[m.end():marks[i+1].start() if i+1 < len(marks) else len(body)])
            for i, m in enumerate(marks)]

def neighbors(i, n=4):
    x, y = i % n, i // n
    return {ny*n+nx for ny in range(max(0,y-1),min(n,y+2))
            for nx in range(max(0,x-1),min(n,x+2)) if (nx,ny)!=(x,y)}

def reveal(i, opened, mines):
    queue = deque([i])
    while queue:
        j = queue.popleft()
        if j in opened or j in mines:
            continue
        opened.add(j)
        if not (neighbors(j) & mines):
            queue.extend(neighbors(j))

class Chapter22And23Review(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(sections(22)), 16)
        self.assertEqual(len(sections(23)), 5)

    def test_local_inference_has_four_outcomes_and_narrow_law(self):
        code = read("src/14_local_inference.bend")
        body = dict(sections(22))["最小の推論規則をBend 2で書く"]
        for s in ("infer(0, 3)", "infer(3, 3)", "infer(1, 3)",
                  "infer(4, 2)", "law zero_remaining_is_safe_for_three"):
            self.assertIn(s, code)
        self.assertIn(r"出力は\textbf{10}", body)
        self.assertIn("盤面全体を証明したものではありません", body)

    def test_manual_transfer_is_not_automatic_fixed_point(self):
        manual = read("minesweeper/nxn_public_three_step.bend")
        fixed = read("minesweeper/nxn_public_many_fixpoint.bend")
        self.assertIn("first() + second() + third()", manual)
        for s in ("type Clue is Data:", "def one_round(", "def iterate("):
            self.assertIn(s, fixed)
        body = dict(sections(22))["公開数字をリストで渡し、固定点まで繰り返す"]
        for s in ("19,683", "8,631", "1,672", "19条件", "Limit"):
            self.assertIn(s, body)

    def test_python_certificate_checker_does_not_import_producer(self):
        producer = read("scripts/emit_single_clue_witness.py")
        checker = read("scripts/audit_single_clue_witness.py")
        self.assertIn("from nxn_single_clue_certificate import certify", producer)
        self.assertIn("from nxn_single_clue_checker import Deduction, replay", checker)
        self.assertNotIn("from nxn_single_clue_certificate import", checker)
        self.assertIn("盤面全体に整合する地雷配置",
                      dict(sections(22))["推論の証明書を、別の処理で検査する"])

    def test_two_clue_difference_is_not_general_solver(self):
        code = read("minesweeper/nxn_public_pair_gap.bend")
        self.assertIn("Subset.infer(", code)
        self.assertIn("[0, 2, 3, 5, 6, 7, 8]", code)
        body = dict(sections(22))["二数字の差集合で、固定点の先へ進む"]
        for s in ("203", "560", "48", "未知近傍集合を手で渡す"):
            self.assertIn(s, body)

    def test_independent_four_by_four_model_count(self):
        models = [set(pair) for pair in combinations(range(16), 1)
                  if 0 not in pair and len(neighbors(0) & set(pair)) == 1]
        self.assertEqual(models, [{1}, {4}, {5}])
        self.assertTrue(all(15 not in model for model in models))
        self.assertEqual(len(list(combinations(range(16), 2))), 120)

    def test_public_bitmasks_and_bounded_three_clue_solver(self):
        code = read("minesweeper/public_solver.bend")
        self.assertIn("Public{opened: List<&2, Number>}", code)
        self.assertIn("U32.is_eq(count, 0)", code)
        self.assertIn("Solver.Number{15, 0}", read("minesweeper/public_two_corners.bend"))
        self.assertEqual(sum(1 << i for i in (1,4,5,10,11,14)), 19506)
        bridge = read("minesweeper/nxn_public_three_bridge.bend")
        self.assertIn("with_total_guard", bridge)
        self.assertIn("n * n - Sets.size(revealed)", bridge)
        body = dict(sections(22))["公開数字三つをBendの推論器へつなぐ"]
        for s in ("341", "候補数は2", "True{}", "False{}"):
            self.assertIn(s, body)

    def test_independent_replay_of_fixed_no_guess_certificate(self):
        mines, opened = {13, 15}, set()
        self.assertEqual(sum(1 << i for i in mines), 40960)
        counts = []
        for click in (0, 12, 14):
            self.assertNotIn(click, mines)
            reveal(click, opened, mines)
            counts.append(len(opened))
        self.assertEqual(counts, [12, 13, 14])
        self.assertEqual(opened, set(range(16)) - mines)
        generator = read("minesweeper/noguess_generator.bend")
        self.assertIn("Session.click(Session.new(mask), 0)", generator)
        self.assertIn("Solver.provably_safe(visible)", generator)
        self.assertIn("continue_play(16n", generator)
        body = dict(sections(22))["候補盤面を実際に解いてから採用する"]
        self.assertIn("mines=40960;moves=0,12,14", body)
        self.assertIn("4×4、地雷2個", body)

    def test_final_api_pipeline_and_three_distinct_gates(self):
        code = read("src/17_list_pipeline.bend")
        for s in ("List.range(4n)", "Nat.is_lt(n, 3n)", "List.filter", "List.foldl"):
            self.assertIn(s, code)
        self.assertEqual(sum(i for i in range(4) if i < 3), 3)
        self.assertIn("3n", dict(sections(23))["知らない関数を最小例で試す"])
        body = dict(sections(23))["三つの確認を一緒にしない"]
        for s in ("型検査", "実行テスト", "形式的証明"):
            self.assertIn(s, body)

if __name__ == "__main__":
    unittest.main()
