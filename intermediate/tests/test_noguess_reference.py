"""Check the reference solver using independent enumerated small boards."""
from itertools import combinations
from unittest import TestCase
from unittest.mock import patch

from intermediate.solutions.noguess_reference import (
    GenerationFailed, Visible, consistent_models, expose, generate,
    neighbors, provably_safe, verify_no_guess,
)


class ReferenceNoGuessTests(TestCase):
    def test_non_warping_neighbors(self):
        self.assertEqual(set(neighbors(0, 4, 4)), {1, 4, 5})
        self.assertEqual(len(neighbors(5, 4, 4)), 8)
        self.assertNotIn(15, neighbors(0, 4, 4))

    def test_visible_deduction_rejects_guess(self):
        # One visible '1'; three covered neighbors are symmetric.
        view = Visible(2, 2, 1, ((0, 1),))
        self.assertEqual(len(consistent_models(view)), 3)
        self.assertEqual(provably_safe(view), frozenset())

    def test_visible_model_consistency_and_safety(self):
        first = 0
        protected = {first, *neighbors(first, 4, 4)}
        candidates = sorted(set(range(16)) - protected)
        successes = 0
        for positions in combinations(candidates, 2):
            mines = frozenset(positions)
            view = expose(mines, Visible(4, 4, 2, ()), first)
            models = consistent_models(view)
            self.assertIn(mines, models)
            self.assertTrue(provably_safe(view).isdisjoint(mines))
            trace = verify_no_guess(4, 4, mines, first)
            if trace is not None:
                successes += 1
                self.assertEqual(trace[0], first)
                self.assertTrue(set(trace).isdisjoint(mines))
        self.assertGreater(successes, 0)

    def test_generation_returns_verified_board(self):
        mines, trace = generate(4, 4, 2, 0, seed=2026)
        self.assertEqual(len(mines), 2)
        self.assertEqual(trace, verify_no_guess(4, 4, mines, 0))
        self.assertEqual((mines, trace), generate(4, 4, 2, 0, seed=2026))

    def test_exhaustion_is_explicit(self):
        with patch("intermediate.solutions.noguess_reference.verify_no_guess",
                   return_value=None):
            with self.assertRaises(GenerationFailed):
                generate(4, 4, 2, 0, seed=2026, attempts=3)

    def test_rejects_impossible_mine_count(self):
        with self.assertRaises(ValueError):
            generate(2, 2, 1, 0, seed=0)
