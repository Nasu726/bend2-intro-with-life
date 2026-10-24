"""No-guess candidate screening versus an independent whole-board solver."""
from itertools import combinations
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
from nxn_board_oracle import click, neighbors, new_game, public_view
from nxn_noguess_replay import Replay, check_candidate
from nxn_public_inference import infer as real_infer


def brute_safe(view):
    """Whole-board enumeration: no frontier, components or DP."""
    opened = dict(view.opened)
    hidden = set(range(view.n * view.n)) - opened.keys()
    models = []
    for combo in combinations(sorted(hidden), view.mine_count):
        mines = set(combo)
        if all(sum(j in mines for j in neighbors(view.n, i)) == clue
               for i, clue in opened.items()):
            models.append(mines)
    if not models:
        raise AssertionError("a real board cannot contradict its clues")
    return sorted(hidden - set.union(*models) - view.flags)


def brute_replay(n, mines, first):
    if first in mines:
        return Replay("first_mine")
    state = click(new_game(n, mines), first)
    clicks = [first]
    while state.phase != "Won":
        choices = brute_safe(public_view(state))
        if not choices:
            return Replay("stuck", tuple(clicks), len(state.opened))
        state = click(state, choices[0])
        if state.phase == "Lost":
            raise AssertionError("oracle clicked a mine")
        clicks.append(choices[0])
    return Replay("accepted", tuple(clicks), len(state.opened))


class NoGuessReplay(unittest.TestCase):
    def test_exhaustive_two_and_three_by_three(self):
        checked = 0
        for n in (2, 3):
            for mask in range(1 << (n*n)):
                mines = frozenset(i for i in range(n*n) if mask >> i & 1)
                if len(mines) == n*n:
                    continue
                for first in range(n*n):
                    actual = check_candidate(n, mines, first)
                    self.assertEqual(actual, brute_replay(n, mines, first),
                                     (n, mask, first))
                    checked += 1
        self.assertEqual(checked, 4659)

    def test_sampled_four_by_four(self):
        rng = random.Random(20261024)
        for _ in range(100):
            mines = frozenset(rng.sample(range(16), rng.randrange(0, 5)))
            first = rng.randrange(16)
            self.assertEqual(check_candidate(4, mines, first),
                             brute_replay(4, mines, first))

    def test_documented_four_by_four_trace(self):
        self.assertEqual(check_candidate(4, frozenset({1, 5}), 0),
                         Replay("accepted", (0, 2, 3, 4), 14))
        self.assertEqual(check_candidate(3, frozenset({0, 2}), 4),
                         Replay("stuck", (4,), 1))

    def test_limit_and_input_validation(self):
        self.assertEqual(check_candidate(5, frozenset({1, 6}), 0,
                                         max_frontier=2).status, "limit")
        self.assertEqual(check_candidate(3, frozenset({0}), 0).status,
                         "first_mine")
        self.assertEqual(check_candidate(3, frozenset(), 0),
                         Replay("accepted", (0,), 9))
        for args in ((3, frozenset({0}), True, 18),
                     (3, frozenset(), 9, 18),
                     (3, frozenset(), 0, 25),
                     (3, frozenset(), 0, True),
                     (3, frozenset({9}), 0, 18)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                check_candidate(*args)

    def test_solver_receives_public_view_only(self):
        calls = []
        def spy(n, mine_count, opened, flags, max_frontier):
            calls.append((n, mine_count, opened, flags, max_frontier))
            return real_infer(n, mine_count, opened, flags,
                              max_frontier=max_frontier)
        with patch("nxn_noguess_replay.infer", side_effect=spy):
            result = check_candidate(2, frozenset({1}), 0)
        self.assertEqual(result.status, "stuck")
        self.assertEqual(calls, [(2, 1, ((0, 1),), frozenset(), 18)])


if __name__ == "__main__":
    unittest.main()
