"""Independent finite-model checks for public two-clue fixed-point inference."""
from itertools import combinations
from random import Random
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_pairwise_propagation import infer_pairwise_clue_certainties
from nxn_single_clue_propagation import infer_single_clue_certainties


def oracle_neighbors(n, cell):
    return {j for j in range(n*n) if j != cell and
            abs(j % n - cell % n) <= 1 and
            abs(j // n - cell // n) <= 1}


def models(n, opened, initial_mines, initial_safe):
    shown = {cell for cell, _ in opened}
    free = sorted(set(range(n*n)) - shown - initial_mines - initial_safe)
    result = []
    for k in range(len(free) + 1):
        for cells in combinations(free, k):
            mine_set = initial_mines | set(cells)
            if all(len(mine_set & oracle_neighbors(n, cell)) == clue
                   for cell, clue in opened):
                result.append(mine_set)
    return result


class PairwisePropagation(unittest.TestCase):
    def test_two_clues_force_cells_that_single_clues_cannot(self):
        opened = ((1, 1), (4, 1))
        self.assertEqual(infer_single_clue_certainties(3, opened), ((), ()))
        self.assertEqual(infer_pairwise_clue_certainties(3, opened),
                         ((), (6, 7, 8)))
        self.assertEqual(infer_pairwise_clue_certainties(
            3, opened, certified_safe=(6, 7, 8)), ((), (6, 7, 8)))

    def test_single_clue_chain_remains_available(self):
        self.assertEqual(infer_pairwise_clue_certainties(
            3, ((0, 0), (2, 1), (6, 1))), ((5, 7), (1, 3, 4)))

    def test_validation_and_conflicting_evidence(self):
        for args in (
            (3, ((0, 0), (0, 1))),
            (3, ((0, True),)),
            (3, ((0, 0),), (1,)),
            (3, ((0, 0),), (), (0,)),
            (3, ((0, 0),), (2,), (2,)),
            (101, ((0, 0),)),
            (3, None),
            (3, ((0, 0),), None),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                infer_pairwise_clue_certainties(*args)

    def test_independent_exhaustive_three_by_three_soundness(self):
        rng = Random(20261026)
        for trial in range(240):
            actual = set(rng.sample(range(9), rng.randrange(5)))
            available = sorted(set(range(9)) - actual)
            shown = set(rng.sample(available, min(3, len(available))))
            opened = tuple((cell, len(actual & oracle_neighbors(3, cell)))
                           for cell in sorted(shown))
            hidden_safe = sorted(set(range(9)) - actual - shown)
            initial_mines = set(rng.sample(
                sorted(actual), rng.randrange(len(actual) + 1)))
            initial_safe = set(rng.sample(
                hidden_safe, rng.randrange(len(hidden_safe) + 1)))
            mine_result, safe_result = infer_pairwise_clue_certainties(
                3, opened, sorted(initial_mines), sorted(initial_safe))
            possibilities = models(3, opened, initial_mines, initial_safe)
            self.assertTrue(possibilities, trial)
            self.assertLessEqual(set(mine_result), set.intersection(*possibilities))
            self.assertLessEqual(set(safe_result),
                                 set(range(9)) - set.union(*possibilities))
            single_mines, single_safe = infer_single_clue_certainties(
                3, opened, sorted(initial_mines), sorted(initial_safe))
            self.assertLessEqual(set(single_mines), set(mine_result))
            self.assertLessEqual(set(single_safe), set(safe_result))
            self.assertEqual((mine_result, safe_result),
                             infer_pairwise_clue_certainties(
                                 3, opened, mine_result, safe_result))

    def test_large_revealed_board_without_quadratic_pair_scan(self):
        # 100x100 revealed zeros have no hidden neighbors and no deductions.
        self.assertEqual(infer_pairwise_clue_certainties(
            100, ((i, 0) for i in range(10000))), ((), ()))


if __name__ == "__main__":
    unittest.main()
