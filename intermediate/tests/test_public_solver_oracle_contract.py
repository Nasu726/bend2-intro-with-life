"""Metamorphic checks for the oracle used to judge the Bend public solver.

These tests do not prove the Bend implementation. They ensure that the
independent Python expected-value generator never marks a true mine safe
when given authentic public clues, and that adding a clue cannot revoke
an already-proven safe unopened square.
"""
from itertools import combinations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_public_solver import neighbors, oracle


def observed(mines, cell):
    return (cell, len(neighbors(cell) & mines))


class PublicSolverOracleContract(unittest.TestCase):
    def test_all_1680_single_reveals_are_safe(self):
        count = 0
        for pair in combinations(range(16), 2):
            mines = set(pair)
            mine_bits = sum(1 << cell for cell in mines)
            for cell in range(16):
                if cell in mines:
                    continue
                safe_bits = oracle([observed(mines, cell)])
                with self.subTest(mines=pair, cell=cell):
                    self.assertNotEqual(safe_bits, 65536)
                    self.assertEqual(safe_bits & mine_bits, 0)
                    self.assertEqual(safe_bits & (1 << cell), 0)
                count += 1
        self.assertEqual(count, 1680)

    def test_extra_true_clue_cannot_remove_prior_safe_cells(self):
        checked = 0
        for pair in combinations(range(16), 2):
            mines = set(pair)
            first = next(i for i in range(16) if i not in mines)
            one = [observed(mines, first)]
            before = oracle(one)
            self.assertNotEqual(before, 65536)
            for second in range(16):
                if second in mines or second == first:
                    continue
                after = oracle(one + [observed(mines, second)])
                with self.subTest(mines=pair, second=second):
                    self.assertNotEqual(after, 65536)
                    self.assertEqual(before & ~(1 << second) & ~after, 0)
                checked += 1
        self.assertEqual(checked, 1560)

    def test_contradictory_observations_are_not_certified(self):
        for view in ([(0, 0), (0, 1)], [(0, 0), (16, 0)],
                     [(0, 9)], [(15, 1), (15, 2)]):
            with self.subTest(view=view):
                self.assertEqual(oracle(view), 65536)


if __name__ == "__main__":
    unittest.main()
