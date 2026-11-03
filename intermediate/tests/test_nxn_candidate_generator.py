"""Independent finite checks for the bounded N x N candidate generator."""
from itertools import combinations
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
from nxn_candidate_generator import Certificate, Generation, generate
from nxn_board_oracle import click, neighbors, new_game, public_view
from nxn_noguess_replay import Replay


def brute_safe(view):
    """Enumerate full boards, independently of the frontier/DP inference."""
    opened = dict(view.opened)
    hidden = set(range(view.n * view.n)) - opened.keys()
    valid = []
    for placement in combinations(sorted(hidden), view.mine_count):
        mine_set = set(placement)
        if all(sum(j in mine_set for j in neighbors(view.n, i)) == clue
               for i, clue in opened.items()):
            valid.append(mine_set)
    if not valid:
        raise AssertionError("actual clues have no possible mine placement")
    return sorted(hidden - set.union(*valid) - view.flags)


def brute_replay(n, mines, first):
    state = click(new_game(n, frozenset(mines)), first)
    moves = [first]
    while state.phase != "Won":
        safe = brute_safe(public_view(state))
        if not safe:
            return None
        state = click(state, safe[0])
        if state.phase == "Lost":
            raise AssertionError("brute-safe clicked a mine")
        moves.append(safe[0])
    return Certificate(tuple(sorted(mines)), tuple(moves), len(state.opened))


class CandidateGenerator(unittest.TestCase):
    def test_exhaustive_two_and_three_by_three_against_whole_board(self):
        checked = 0
        for n in (2, 3):
            for mine_count in range(n*n):
                for first in range(n*n):
                    expected = None
                    for placement in combinations(
                            (i for i in range(n*n) if i != first), mine_count):
                        expected = brute_replay(n, placement, first)
                        if expected is not None:
                            break
                    actual = generate(n, mine_count, first,
                                      max_candidates=100000)
                    self.assertEqual(actual.possible,
                                     len(list(combinations(range(n*n-1), mine_count))))
                    if expected is None:
                        self.assertEqual(actual.status, "no_match")
                        self.assertIsNone(actual.certificate)
                        self.assertEqual(actual.examined, actual.possible)
                    else:
                        self.assertEqual(actual.status, "accepted")
                        self.assertEqual(actual.certificate, expected)
                    checked += 1
        self.assertEqual(checked, 97)

    def test_documented_witness_and_no_match(self):
        accepted = generate(4, 2, 0)
        self.assertEqual(accepted.status, "accepted")
        self.assertEqual(accepted.possible, 105)
        self.assertEqual(accepted.examined, 3)
        self.assertEqual(accepted.stuck, 2)
        witness = accepted.certificate
        self.assertIsNotNone(witness)
        self.assertNotIn(0, witness.mines)
        self.assertEqual(witness, Certificate((1, 4), (0, 2, 3), 14))
        self.assertEqual(witness, brute_replay(4, witness.mines, 0))
        self.assertEqual(generate(2, 1, 0),
                         Generation("no_match", 3, 3, 3, 0))
        self.assertEqual(generate(3, 0, 0).certificate,
                         Certificate((), (0,), 9))

    def test_budget_and_inconclusive_distinguished(self):
        with patch("nxn_candidate_generator.check_candidate",
                   return_value=Replay("limit")) as fake:
            budget = generate(2, 1, 0, max_candidates=2, max_frontier=0)
            self.assertEqual(budget, Generation("budget", 2, 3, 0, 2))
            self.assertEqual(fake.call_count, 2)
            self.assertEqual(fake.call_args.kwargs, {"max_frontier": 0})
            all_tried = generate(2, 1, 0, max_candidates=3)
            self.assertEqual(all_tried,
                             Generation("inconclusive", 3, 3, 0, 3))

    def test_first_click_excluded_and_early_stop(self):
        seen = []
        def fake(n, mines, first, max_frontier):
            seen.append(tuple(sorted(mines)))
            return Replay("accepted", (first,), n*n-1) if len(seen) == 2 \
                else Replay("stuck", (first,), 1)
        with patch("nxn_candidate_generator.check_candidate", side_effect=fake):
            result = generate(3, 2, 4)
        self.assertEqual(seen, [(0, 1), (0, 2)])
        self.assertEqual(result,
                         Generation("accepted", 2, 28, 1, 0,
                                    Certificate((0, 2), (4,), 8)))

    def test_size_and_input_boundaries(self):
        self.assertEqual(generate(100, 9999, 0),
                         Generation("accepted", 1, 1, 0, 0,
                                    Certificate(tuple(range(1, 10000)), (0,), 1)))
        for args in ((1, 0, 0), (101, 0, 0), (True, 0, 0),
                     (3, True, 0), (3, -1, 0), (3, 9, 0),
                     (3, 0, True), (3, 0, 9), (3, 0, -1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                generate(*args)
        for kwargs in ({"max_candidates": 0}, {"max_candidates": True},
                       {"max_candidates": 100001}, {"max_frontier": -1},
                       {"max_frontier": 25}, {"max_frontier": False}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                generate(3, 1, 0, **kwargs)

    def test_unexpected_replay_state_rejected(self):
        for bad in ("first_mine", "contradiction", "other"):
            with patch("nxn_candidate_generator.check_candidate",
                       return_value=Replay(bad)):
                with self.subTest(bad=bad), self.assertRaises(AssertionError):
                    generate(2, 1, 0)


if __name__ == "__main__":
    unittest.main()
