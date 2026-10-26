"""Independent certificate replay and finite 3x3 mine-layout model checks."""
from itertools import combinations
from pathlib import Path
from random import Random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_single_clue_certificate import Deduction, certify, replay


def independent_neighbors(n, cell):
    return {other for other in range(n*n) if other != cell
            and abs(other % n - cell % n) <= 1
            and abs(other // n - cell // n) <= 1}


def independent_models(n, opened, initial_mines=(), initial_safe=()):
    shown = {i for i, _ in opened}
    unexplored = sorted(set(range(n*n)) - shown - set(initial_mines) - set(initial_safe))
    models = []
    for k in range(len(unexplored)+1):
        for positions in combinations(unexplored, k):
            candidate = set(initial_mines) | set(positions)
            if all(len(candidate & independent_neighbors(n, cell)) == clue
                   for cell, clue in opened):
                models.append(candidate)
    return models


class CertificateTests(unittest.TestCase):
    def test_two_round_chain_and_replay(self):
        shown = ((0, 0), (2, 1), (6, 1))
        mines, safe, proof = certify(3, shown)
        self.assertEqual((mines, safe), ((5, 7), (1, 3, 4)))
        self.assertEqual(replay(3, shown, (), (), proof), (mines, safe))
        self.assertTrue(proof)
        # Partial traces cannot masquerade as completed fixed-point certificates.
        with self.assertRaises(ValueError):
            replay(3, shown, (), (), proof[:-1])
        with self.assertRaises(ValueError):
            replay(3, shown, (), (), proof + proof[:1])

    def test_forged_certificate_rejected(self):
        shown = ((0, 0), (2, 1), (6, 1))
        fake = [
            (Deduction(8, safe=(1,)),),
            (Deduction(0, safe=(2,)),),
            (Deduction(0, mines=(1,)),),
            (Deduction(0, safe=(1, 1)),),
            (Deduction(0, safe=(3, 1)),),
            (Deduction(0, safe=(True,)),),
            (Deduction(True, safe=(1,)),),
            (Deduction(0),),
            ("not a deduction",),
        ]
        for attempted in fake:
            with self.subTest(attempted=attempted):
                with self.assertRaises(ValueError):
                    replay(3, shown, (), (), attempted)
        with self.assertRaises(ValueError):
            replay(3, shown, (), (), None)

    def test_replay_with_independently_certified_cells(self):
        shown = ((0, 1),)
        mines, safe, proof = certify(3, shown, (1,), ())
        self.assertEqual(mines, (1,))
        self.assertEqual(safe, (3, 4))
        self.assertEqual(replay(3, shown, (1,), (), proof), (mines, safe))
        self.assertEqual(replay(3, shown, mines, safe, ()), (mines, safe))

    def test_3x3_randomized_soundness_against_all_models(self):
        rng = Random(20261026)
        for trial in range(260):
            actual = set(rng.sample(range(9), rng.randrange(5)))
            shown = tuple(sorted(rng.sample(sorted(set(range(9))-actual),
                                           min(3, 9-len(actual)))))
            opened = tuple((cell, len(actual & independent_neighbors(3, cell)))
                           for cell in shown)
            hidden_safe = sorted(set(range(9))-actual-set(shown))
            given_mines = tuple(sorted(rng.sample(sorted(actual), rng.randrange(len(actual)+1))))
            given_safe = tuple(sorted(rng.sample(hidden_safe, rng.randrange(len(hidden_safe)+1))))
            mines, safe, trace = certify(3, opened, given_mines, given_safe)
            self.assertEqual(replay(3, opened, given_mines, given_safe, trace), (mines, safe))
            models = independent_models(3, opened, given_mines, given_safe)
            self.assertTrue(models)
            self.assertTrue(set(mines) <= set.intersection(*models))
            self.assertTrue(set(safe).isdisjoint(set.union(*models)))
            self.assertLessEqual(len(trace), 9-len(shown)-len(given_mines)-len(given_safe))

    def test_100x100_near_border_no_truth_leakage(self):
        n, cell = 100, 9999
        opened = ((cell, 0),)
        mines, safe, trace = certify(n, opened)
        self.assertEqual(mines, ())
        self.assertEqual(safe, (9898, 9899, 9998))
        self.assertEqual(replay(n, opened, (), (), trace), (mines, safe))


if __name__ == "__main__":
    unittest.main()
