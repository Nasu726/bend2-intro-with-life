"""Independent finite checks for the exact public frontier inference oracle.

These are Python reference checks, NOT Bend tests or general proofs.
"""
from itertools import combinations
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import noguess_reference as slow
import nxn_frontier_solver as fast


class FrontierSolverContracts(unittest.TestCase):
    def test_four_by_four_exhaustive_first_views_against_full_enumeration(self):
        # Every 2-mine layout and every safe first click: 120 * 14 = 1680.
        for pair in combinations(range(16), 2):
            mines = frozenset(pair)
            for first in set(range(16)) - mines:
                view = slow.expose(mines, slow.Visible(4, 4, 2, ()), first)
                with self.subTest(mines=pair, first=first):
                    self.assertEqual(fast.provably_safe_frontier(view),
                                     slow.provably_safe(view))

    def test_ten_by_ten_zero_corner_and_global_budget(self):
        view = slow.Visible(10, 10, 10, ((0, 0),))
        self.assertEqual(fast.provably_safe_frontier(view),
                         frozenset({1, 10, 11}))
        # Two disconnected corner clues; exactly two mines among six frontier
        # cells, hence all 92 other hidden cells are forced safe.
        corners = slow.Visible(10, 10, 2, ((0, 1), (99, 1)))
        self.assertEqual(fast.provably_safe_frontier(corners),
                         slow.provably_safe(corners, limit=5000))
        self.assertEqual(len(fast.provably_safe_frontier(corners)), 92)
        # An additional mine may be anywhere outside the frontier.
        extra = slow.Visible(10, 10, 3, ((0, 1), (99, 1)))
        self.assertEqual(fast.provably_safe_frontier(extra), frozenset())

    def test_ten_by_ten_single_mine_exhaustive_oracle(self):
        # Independent naive enumeration: only 99 candidate placements.
        for first in (0, 11, 44, 99):
            for clue in range(0, 2):
                view = slow.Visible(10, 10, 1, ((first, clue),))
                with self.subTest(first=first, clue=clue):
                    self.assertEqual(fast.provably_safe_frontier(view),
                                     slow.provably_safe(view))

    def test_ten_by_ten_nontrivial_certificate_against_full_oracle(self):
        # This is a finite 10x10, two-mine certificate, not a general guarantee.
        mines = frozenset({88, 99})
        trace = fast.verify_no_guess_frontier(10, 10, mines, 0)
        self.assertEqual(trace, (0, 89, 98))
        view = slow.expose(mines, slow.Visible(10, 10, 2, ()), trace[0])
        for move in trace[1:]:
            # Independent complete layout enumeration: C(100,2) = 4,950.
            self.assertIn(move, slow.provably_safe(view, limit=5000))
            view = slow.expose(mines, view, move)
        self.assertEqual(len(view.opened), 98)

    def test_invalid_and_inconsistent_public_information(self):
        invalid = (
            slow.Visible(10, 10, 101, ()),
            slow.Visible(10, 10, 2, ((100, 0),)),
            slow.Visible(10, 10, 2, ((0, 4),)),
            slow.Visible(10, 10, 2, ((0, 0), (0, 1))),
            slow.Visible(2, 2, 2, ((0, 0), (1, 0), (2, 0))),
            slow.Visible(True, 10, 2, ()),
            slow.Visible(10, 10, True, ()),
            slow.Visible(10, 10, 2, ((False, 0),)),
        )
        for view in invalid:
            with self.subTest(view=view), self.assertRaises(ValueError):
                fast.provably_safe_frontier(view)
        with self.assertRaises(ValueError):
            fast.provably_safe_frontier(slow.Visible(4, 4, 2, ()), node_limit=0)
        with self.assertRaises(ValueError):
            fast.provably_safe_frontier(slow.Visible(4, 4, 2, ()), node_limit=True)
        # Duplicate identical clues are idempotent, not inconsistent.
        view = slow.Visible(4, 4, 2, ((0, 0), (0, 0)))
        self.assertEqual(fast.provably_safe_frontier(view),
                         fast.provably_safe_frontier(slow.Visible(4, 4, 2, ((0, 0),))))

    def test_budget_exhaustion_never_produces_partial_certificate(self):
        view = slow.Visible(4, 4, 2, ((5, 1),))
        with self.assertRaises(slow.SearchLimit):
            fast.provably_safe_frontier(view, node_limit=1)
        self.assertIsNone(fast.verify_no_guess_frontier(
            4, 4, frozenset({13, 15}), 0, node_limit=1))

    def test_replay_matches_small_reference_and_rejects_guess(self):
        self.assertEqual(fast.verify_no_guess_frontier(
            4, 4, frozenset({13, 15}), 0), (0, 12, 14))
        self.assertEqual(fast.verify_no_guess_frontier(
            10, 10, frozenset(), 0), (0,))
        self.assertIsNone(fast.verify_no_guess_frontier(
            10, 10, frozenset({99}), 99))
        for invalid in (False, -1, 100):
            with self.subTest(first=invalid), self.assertRaises(ValueError):
                fast.verify_no_guess_frontier(10, 10, frozenset({99}), invalid)

    def test_random_small_public_views_against_naive_oracle(self):
        rng = random.Random(20261023)
        for n in (3, 4):
            for _ in range(100):
                mine_count = rng.randint(0, min(n * n - 1, 3))
                mines = frozenset(rng.sample(range(n * n), mine_count))
                first = rng.choice(sorted(set(range(n * n)) - mines))
                view = slow.expose(mines, slow.Visible(n, n, mine_count, ()), first)
                self.assertEqual(fast.provably_safe_frontier(view),
                                 slow.provably_safe(view))


if __name__ == "__main__":
    unittest.main()
