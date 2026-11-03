"""Independent finite public-only checks for the four-clue fixed-point model.

The truth-layout oracle is separate from the reference deduction rules.
No flag or hidden mine layout is passed to the solver.
"""
from itertools import combinations
from pathlib import Path
from random import Random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_public_four_fixpoint import fixtures, model


def full_neighbors(n, i):
    return {j for j in range(n*n) if j != i
            and abs(j % n - i % n) <= 1
            and abs(j // n - i // n) <= 1}


def compatible(n, public, certified_mines, certified_safe):
    shown = {i for i, _ in public}
    remaining = sorted(set(range(n*n)) - shown - certified_mines - certified_safe)
    for size in range(len(remaining)+1):
        for extra in combinations(remaining, size):
            mines = set(certified_mines) | set(extra)
            if all(len(mines & full_neighbors(n, i)) == value
                   for i, value in public):
                yield mines


class FourClueReference(unittest.TestCase):
    def test_fourth_clue_adds_new_safe_cells(self):
        first = fixtures()[0]
        self.assertEqual(first[1], ((1, 1), (2, 0), (4, 1), (5, 0)))
        self.assertEqual(model(*first), ((), (1, 2, 4, 5, 7, 8)))

    def test_soundness_against_independent_complete_models(self):
        rng = Random(20261028)
        for trial in range(160):
            truth = set(rng.sample(range(9), rng.randrange(5)))
            available = sorted(set(range(9)) - truth)
            revealed = tuple(sorted(rng.sample(available, 4)))
            public = tuple((i, len(truth & full_neighbors(3, i)))
                           for i in revealed)
            extra_safe = sorted(set(range(9)) - truth - set(revealed))
            given_mines = tuple(sorted(rng.sample(sorted(truth), rng.randrange(len(truth)+1))))
            given_safe = tuple(sorted(rng.sample(extra_safe, rng.randrange(len(extra_safe)+1))))
            found = model(3, public, given_mines, given_safe)
            self.assertIsNotNone(found, trial)
            all_models = list(compatible(3, public, set(given_mines), set(given_safe)))
            self.assertTrue(all_models, trial)
            mine_intersection = set.intersection(*all_models)
            mine_union = set.union(*all_models)
            self.assertLessEqual(set(found[0]), mine_intersection)
            self.assertTrue(set(found[1]).isdisjoint(mine_union))

    def test_model_rejects_invalid_evidence(self):
        public = ((1, 1), (2, 0), (4, 1), (5, 0))
        for n, shown, mines, safe in (
            (1, public, (), ()),
            (101, public, (), ()),
            (3, public[:3], (), ()),
            (3, public[:3]+(public[1],), (), ()),
            (3, public, (1,), ()),
            (3, public, (), (9,)),
            (3, public, (), (True,)),
        ):
            with self.subTest(n=n, shown=shown, mines=mines, safe=safe):
                self.assertIsNone(model(n, shown, mines, safe))


if __name__ == "__main__":
    unittest.main()
