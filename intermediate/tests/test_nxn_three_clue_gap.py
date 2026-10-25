"""Regression: three public clues can force a cell when no pair can.

The expected models come from whole-board combinations, not the frontier
solver's component or pairwise-bound algorithms. This is a finite test.
"""
from itertools import combinations
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_three_clue_oracle import CLUES, MINE_COUNT, deductions, enumerate_models, neighbors
from nxn_public_inference import infer


class ThreeClueGap(unittest.TestCase):
    def test_real_three_by_three_clues_and_models(self):
        # One actual board has mines at 1 and 6. Both hidden placements below
        # are consistent with the *same* three public clues.
        self.assertEqual(tuple(len({1, 6} & neighbors(3, i)) for i, _ in CLUES),
                         (1, 1, 1))
        self.assertEqual(enumerate_models(3, MINE_COUNT, CLUES),
                         ((1, 6), (1, 8)))
        self.assertEqual(deductions(3, MINE_COUNT, CLUES),
                         ("ok", (3, 4, 5), (1,), 2))

    def test_no_pair_forces_a_cell_but_three_do(self):
        for pair in combinations(CLUES, 2):
            with self.subTest(clues=pair):
                status, safe, mines, model_count = deductions(3, MINE_COUNT, pair)
                self.assertEqual(status, "ok")
                self.assertGreater(model_count, 1)
                self.assertEqual((safe, mines), ((), ()))
                actual = infer(3, MINE_COUNT, pair)
                self.assertEqual((actual.status, actual.safe, actual.forced_mines),
                                 (status, safe, mines))
        actual = infer(3, MINE_COUNT, CLUES)
        self.assertEqual((actual.status, actual.safe, actual.forced_mines),
                         ("ok", (3, 4, 5), (1,)))

    def test_all_64_hidden_placements_with_three_public_clues(self):
        hidden = (1, 3, 4, 5, 6, 8)
        for mask in range(1 << len(hidden)):
            mines = {cell for bit, cell in enumerate(hidden) if mask & (1 << bit)}
            observations = tuple((cell, len(mines & neighbors(3, cell)))
                                 for cell, _ in CLUES)
            for chosen in (observations, *combinations(observations, 2)):
                with self.subTest(mask=mask, clues=chosen):
                    status, safe, forced, _ = deductions(3, len(mines), chosen)
                    actual = infer(3, len(mines), chosen, max_frontier=6)
                    self.assertEqual((actual.status, actual.safe, actual.forced_mines),
                                     (status, safe, forced))

    def test_flags_are_not_evidence_and_limits_are_distinct(self):
        flagged_safe = infer(3, MINE_COUNT, CLUES, flags=(3,))
        self.assertEqual((flagged_safe.safe, flagged_safe.forced_mines),
                         ((4, 5), (1,)))
        flagged_mine = infer(3, MINE_COUNT, CLUES, flags=(1,))
        self.assertEqual((flagged_mine.safe, flagged_mine.forced_mines),
                         ((3, 4, 5), (1,)))
        self.assertEqual(infer(3, MINE_COUNT, CLUES, max_frontier=5).status,
                         "limit")
        self.assertEqual(infer(3, MINE_COUNT, CLUES, max_frontier=6).status,
                         "ok")


if __name__ == "__main__":
    unittest.main()
