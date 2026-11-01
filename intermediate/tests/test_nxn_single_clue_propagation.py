"""Independent exhaustive 3x3 oracle for public single-clue propagation."""
from itertools import combinations
from pathlib import Path
from random import Random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_single_clue_propagation import infer_single_clue_certainties


def oracle_neighbors(n, cell):
    x, y = cell % n, cell // n
    return {j for j in range(n * n) if j != cell
            and abs(j % n - x) <= 1 and abs(j // n - y) <= 1}


def all_models(n, opened, initial_mines, initial_safe):
    shown = {cell for cell, _ in opened}
    remaining = sorted(set(range(n*n)) - shown - initial_mines - initial_safe)
    models = []
    for k in range(len(remaining) + 1):
        for subset in combinations(remaining, k):
            mines = initial_mines | set(subset)
            if all(len(mines & oracle_neighbors(n, cell)) == number
                   for cell, number in opened):
                models.append(mines)
    return models


class SingleCluePropagation(unittest.TestCase):
    def test_zero_then_forced_mines_and_idempotence(self):
        # Public 0 at cell 0 proves cells 1,3,4 safe; numbers at 2,6
        # then prove 5 and 7 are mines. No hidden layout is passed in.
        clues = ((0, 0), (2, 1), (6, 1))
        mines, safe = infer_single_clue_certainties(3, clues)
        self.assertEqual(mines, (5, 7))
        self.assertEqual(safe, (1, 3, 4))
        self.assertEqual((mines, safe), infer_single_clue_certainties(
            3, clues, certified_mines=mines, certified_safe=safe))
        # One remaining unknown must not be padded into six Bend bits.
        self.assertEqual(len(set(range(9)) - {0, 2, 6}
                             - set(mines) - set(safe)), 1)

    def test_ambiguous_clue_is_not_a_guess(self):
        self.assertEqual(infer_single_clue_certainties(3, ((0, 1),)),
                         ((), ()))

    def test_invalid_inputs_and_local_contradictions(self):
        bad = [
            (True, ((0, 0),), (), ()),
            (3, ((0, True),), (), ()),
            (3, ((0, 0), (0, 1)), (), ()),
            (3, ((9, 0),), (), ()),
            (3, ((0, 0),), (1,), ()),
            (3, ((0, 0),), (), (1, 1)),
            (3, ((0, 0),), (2,), (2,)),
            (3, ((0, 0),), (), (0,)),
            (3, ((0, 0),), (True,), ()),
            (3, ((0, 0),), (9,), ()),
            (3, ((0, 0),), (), (False,)),
            (3, ((0, 0),), (), None),
            (3, ((0, 0),), None, ()),
            (3, None, (), ()),
            (3, ((0, 0),), (1,), ()),
            (3, ((4, 8), (0, 0), (2, 0)), (), ()),
        ]
        for n, opened, mines, safe in bad:
            with self.subTest(case=(n, opened, mines, safe)):
                with self.assertRaises(ValueError):
                    infer_single_clue_certainties(n, opened, mines, safe)

    def test_independent_exhaustive_model_soundness(self):
        rng = Random(20261026)
        checked = 0
        for _ in range(240):
            actual = set(rng.sample(range(9), rng.randrange(5)))
            shown = tuple(sorted(rng.sample(
                sorted(set(range(9)) - actual),
                min(3, 9 - len(actual)))))
            opened = tuple((cell, len(actual & oracle_neighbors(3, cell)))
                           for cell in shown)
            hidden_safe = sorted(set(range(9)) - actual - set(shown))
            initial_mines = set(rng.sample(
                sorted(actual), rng.randrange(len(actual) + 1)))
            initial_safe = set(rng.sample(
                hidden_safe, rng.randrange(len(hidden_safe) + 1)))
            mines, safe = infer_single_clue_certainties(
                3, opened, sorted(initial_mines), sorted(initial_safe))
            models = all_models(3, opened, initial_mines, initial_safe)
            self.assertTrue(models)
            self.assertTrue(set(mines) <= set.intersection(*models))
            self.assertTrue(set(safe) <= set(range(9)) - set.union(*models))
            self.assertFalse(set(mines) & set(safe))
            checked += 1
        self.assertEqual(checked, 240)


if __name__ == "__main__":
    unittest.main()
