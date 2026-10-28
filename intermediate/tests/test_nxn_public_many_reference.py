"""Finite tests for public-clue propagation with arbitrary clue counts.

The full-layout oracle is independent of the local deduction model. A global
proof, completeness theorem, or general no-guess generator is not claimed.
"""
from itertools import combinations
from pathlib import Path
from random import Random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_public_many_fixpoint import model
from test_nxn_public_three_fixpoint import model as three_model
from test_nxn_public_four_fixpoint import model as four_model


def neighbors(n, index):
    return {j for j in range(n*n) if j != index
            and abs(index % n-j % n) <= 1
            and abs(index // n-j // n) <= 1}


def satisfying(n, public, certified_mines, certified_safe):
    available = set(range(n*n)) - {i for i, _ in public}
    unknown = sorted(available - certified_mines - certified_safe)
    for count in range(len(unknown)+1):
        for choice in combinations(unknown, count):
            mines = set(choice) | certified_mines
            if all(len(neighbors(n,i) & mines) == clue for i,clue in public):
                yield mines


class ManyClueReference(unittest.TestCase):
    def test_160_deterministic_public_only_cases(self):
        rng = Random(20261028)
        for trial in range(160):
            n = 3
            truth = set(rng.sample(range(n*n), rng.randrange(5)))
            safe = sorted(set(range(n*n)) - truth)
            count = rng.randrange(min(len(safe), 6)+1)
            shown = tuple(sorted(rng.sample(safe, count)))
            public = tuple((i, len(truth & neighbors(n,i))) for i in shown)
            extra_safe = tuple(sorted(rng.sample(sorted(set(safe)-set(shown)),
                          rng.randrange(len(safe)-len(shown)+1))))
            known_mines = tuple(sorted(rng.sample(sorted(truth),
                                rng.randrange(len(truth)+1))))
            known_safe = tuple(sorted(set(extra_safe) | set(shown)))
            result = model(n, public, known_mines, known_safe)
            self.assertIsInstance(result, tuple, trial)
            all_models = list(satisfying(n, public, set(known_mines), set(known_safe)))
            self.assertTrue(all_models, trial)
            forced_mines = set.intersection(*all_models)
            possible_mines = set.union(*all_models)
            self.assertLessEqual(set(result[0]), forced_mines, trial)
            self.assertTrue(set(result[1]).isdisjoint(possible_mines), trial)

    def test_matching_existing_three_and_four_models(self):
        rng = Random(642)
        for n, truth in ((3, (0,7)), (4, (3,15)), (5, (12,24))):
            safe = sorted(set(range(n*n)) - set(truth))
            for count, oracle in ((3, three_model), (4, four_model)):
                for _ in range(16):
                    shown = tuple(sorted(rng.sample(safe, count)))
                    public = tuple((i, len(neighbors(n,i) & set(truth))) for i in shown)
                    self.assertEqual(
                        model(n, public, (), shown),
                        oracle(n, public),
                        (n, shown))

    def test_clue_order_and_sufficient_fuel(self):
        # A different sweep order may change intermediate states but must
        # not change the final fixed point. N*N+1 rounds suffice on valid
        # evidence; this checks finite examples, not the general proof.
        rng = Random(20261028)
        for trial in range(64):
            n = 3
            truth = set(rng.sample(range(n*n), rng.randrange(5)))
            safe = sorted(set(range(n*n)) - truth)
            shown = tuple(sorted(rng.sample(safe, rng.randrange(min(6, len(safe))+1))))
            public = tuple((i, len(truth & neighbors(n,i))) for i in shown)
            known_mines = tuple(sorted(rng.sample(sorted(truth),
                                rng.randrange(len(truth)+1))))
            result = model(n, public, known_mines, shown, n*n+1)
            self.assertIsInstance(result, tuple, trial)
            self.assertEqual(result, model(n, public[::-1], known_mines, shown,
                                           n*n+1), trial)
            self.assertEqual(result, model(n, public, known_mines, shown,
                                           n*n+2), trial)

    def test_empty_clues_reject_bad_initial_sets(self):
        # Without any opened digit, a purely local rule would never visit
        # the contradictory entries. The public API must reject them first.
        bad = (
            ((0,), (0,)),
            ((9,), ()),
            ((), (9,)),
            ((0, 0), ()),
            ((), (1, 1)),
            ((2, 1), ()),
            ((), (2, 1)),
        )
        for mines, safe in bad:
            with self.subTest(mines=mines, safe=safe):
                self.assertIsNone(model(3, (), mines, safe, 1))
        self.assertEqual(model(3, (), (0,), (1,), 1), ((0,), (1,)))
        self.assertEqual(model(2, (), (0,), (1,), 5), ((0,), (1,)))

    def test_invalid_evidence_and_fuel(self):
        public = ((1,1),(2,0),(4,1),(5,0))
        safe = (1,2,4,5)
        self.assertEqual(model(3, public, (), safe), ((), (1,2,4,5,7,8)))
        self.assertEqual(model(3, public, (), safe, 0), "Limit")
        self.assertEqual(model(3, public, (), safe, 1), "Limit")
        for n, clues, mines, known_safe in (
            (1, public, (), safe),
            (101, public, (), safe),
            (3, public, (), (1,2,4)),
            (3, public[:3]+(public[1],), (), safe),
            (3, public[:3]+((9,0),), (), (1,2,4,9)),
            (3, public[:3]+((5,8),), (), safe),
            (3, public, (1,), safe),
            (3, public, (), safe+(9,)),
        ):
            with self.subTest(n=n, clues=clues):
                self.assertIsNone(model(n, clues, mines, known_safe))


if __name__ == "__main__":
    unittest.main()
