"""Pure Python regression tests for the independent no-guess oracle.

The Bend solver is separately checked by scripts/test_public_solver.py.
"""
from itertools import combinations
from pathlib import Path
import importlib.util
import sys
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "solutions" / "noguess_reference.py"
spec = importlib.util.spec_from_file_location("noguess_reference", SOURCE)
assert spec and spec.loader
reference = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reference
spec.loader.exec_module(reference)
CELLS = range(16)
PAIRS = tuple(frozenset(p) for p in combinations(CELLS, 2))


def adjacent(index):
    x, y = index % 4, index // 4
    return frozenset(j for j in CELLS if j != index
                     and abs(x - j % 4) <= 1 and abs(y - j // 4) <= 1)


def independent_models(opened):
    if any(i not in CELLS or c < 0 or c > len(adjacent(i)) for i, c in opened):
        return set()
    return {pair for pair in PAIRS
            if all(i not in pair and len(adjacent(i) & pair) == c
                   for i, c in opened)}


def independent_open(mines, existing, clicked):
    result = dict(existing)
    pending = [clicked]
    while pending:
        index = pending.pop(0)
        if index in result:
            continue
        if index in mines:
            raise AssertionError("test attempted to open a mine")
        clue = len(adjacent(index) & mines)
        result[index] = clue
        if clue == 0:
            pending.extend(adjacent(index) - result.keys())
    return result


class ReferenceOracleTests(unittest.TestCase):
    def test_single_clue_models(self):
        for index in (0, 1, 5, 15):
            for clue in range(9):
                opened = ((index, clue),)
                view = reference.Visible(4, 4, 2, opened)
                with self.subTest(opened=opened):
                    self.assertEqual(set(reference.consistent_models(view)),
                                     independent_models(opened))

    def test_invalid_and_contradictory_observations(self):
        for opened in (
            ((16, 0),), ((-1, 0),), ((0, -1),), ((0, 9),),
            ((0, 0), (0, 1)), ((15, 1), (15, 2)),
        ):
            with self.subTest(opened=opened):
                view = reference.Visible(4, 4, 2, opened)
                self.assertEqual(reference.consistent_models(view), [])
                with self.assertRaises(ValueError):
                    reference.provably_safe(view)
        single = reference.Visible(4, 4, 2, ((0, 0),))
        duplicate = reference.Visible(4, 4, 2, ((0, 0), (0, 0)))
        self.assertEqual(reference.consistent_models(single),
                         reference.consistent_models(duplicate))

    def test_flood_all_1680_safe_starts(self):
        for mines in PAIRS:
            for first in CELLS:
                if first in mines:
                    continue
                view = reference.Visible(4, 4, 2, ())
                actual = reference.expose(mines, view, first)
                self.assertEqual(dict(actual.opened),
                                 independent_open(mines, {}, first), (mines, first))
        with self.assertRaises(ValueError):
            reference.expose(PAIRS[0], reference.Visible(4, 4, 2, ()), 16)

    def test_all_120_layout_certificates(self):
        accepted = 0
        for mines in PAIRS:
            trace = reference.verify_no_guess(4, 4, mines, 0)
            if trace is None:
                continue  # Rejected boards carry no no-guess guarantee.
            accepted += 1
            self.assertEqual(trace[0], 0)
            self.assertEqual(len(set(trace)), len(trace))
            opened = {}
            for position, clicked in enumerate(trace):
                self.assertNotIn(clicked, mines)
                if position:
                    models = independent_models(tuple(opened.items()))
                    self.assertTrue(models, (mines, trace))
                    self.assertTrue(all(clicked not in pair for pair in models),
                                    (mines, trace, position))
                opened = independent_open(mines, opened, clicked)
            self.assertEqual(len(opened), 14, (mines, trace))
        self.assertGreater(accepted, 0)
        self.assertEqual(reference.verify_no_guess(4, 4, frozenset({13, 15}), 0),
                         (0, 12, 14))

    def test_limits_and_invalid_clicks(self):
        view = reference.Visible(4, 4, 2, ((0, 0),))
        with self.assertRaises(reference.SearchLimit):
            reference.provably_safe(view, limit=0)
        self.assertIsNone(reference.verify_no_guess(
            4, 4, frozenset({13, 15}), 0, limit=0))
        for bad in (-1, 16):
            with self.assertRaises(ValueError):
                reference.generate(4, 4, 2, bad, seed=2026)
        with self.assertRaises(reference.GenerationFailed):
            reference.generate(4, 4, 3, 0, seed=1, attempts=1)


    def test_invalid_true_board_never_certified(self):
        for mines in (frozenset({-1, 15}), frozenset({0, 16})):
            with self.subTest(mines=mines):
                with self.assertRaises(ValueError):
                    reference.verify_no_guess(4, 4, mines, 1)
                with self.assertRaises(ValueError):
                    reference.expose(mines, reference.Visible(4, 4, 2, ()), 1)
        with self.assertRaises(ValueError):
            reference.expose(frozenset({15}), reference.Visible(4, 4, 2, ()), 0)
        with self.assertRaises(ValueError):
            reference.verify_no_guess(0, 4, frozenset(), 0)

    def test_non_warping_neighbors(self):
        self.assertEqual(set(reference.neighbors(0, 4, 4)), {1, 4, 5})
        self.assertEqual(len(reference.neighbors(5, 4, 4)), 8)
        self.assertNotIn(15, reference.neighbors(0, 4, 4))

    def test_visible_deduction_rejects_guess(self):
        view = reference.Visible(2, 2, 1, ((0, 1),))
        self.assertEqual(len(reference.consistent_models(view)), 3)
        self.assertEqual(reference.provably_safe(view), frozenset())

    def test_visible_model_consistency_and_safety(self):
        first = 0
        protected = {first, *reference.neighbors(first, 4, 4)}
        candidates = sorted(set(range(16)) - protected)
        successes = 0
        for positions in combinations(candidates, 2):
            mines = frozenset(positions)
            view = reference.expose(mines, reference.Visible(4, 4, 2, ()), first)
            models = reference.consistent_models(view)
            self.assertIn(mines, models)
            self.assertTrue(reference.provably_safe(view).isdisjoint(mines))
            trace = reference.verify_no_guess(4, 4, mines, first)
            if trace is not None:
                successes += 1
                self.assertEqual(trace[0], first)
                self.assertTrue(set(trace).isdisjoint(mines))
        self.assertGreater(successes, 0)

    def test_generation_returns_verified_board(self):
        mines, trace = reference.generate(4, 4, 2, 0, seed=2026)
        self.assertEqual(len(mines), 2)
        self.assertEqual(trace, reference.verify_no_guess(4, 4, mines, 0))
        self.assertEqual((mines, trace), reference.generate(4, 4, 2, 0, seed=2026))

    def test_exhaustion_is_explicit(self):
        from unittest.mock import patch
        with patch.object(reference, "verify_no_guess", return_value=None):
            with self.assertRaises(reference.GenerationFailed):
                reference.generate(4, 4, 2, 0, seed=2026, attempts=3)

    def test_rejects_impossible_mine_count(self):
        with self.assertRaises(ValueError):
            reference.generate(2, 2, 1, 0, seed=0)

if __name__ == "__main__":
    unittest.main()
