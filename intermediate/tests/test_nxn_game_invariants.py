"""Finite state-machine contracts for the N x N Python oracle, not Bend proofs.

These tests establish expected behavior before the N x N Bend engine exists.
The independent clue calculation intentionally does not call board.neighbors.
"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_board_oracle as board


def independent_clue(n, mines, i):
    x, y = i % n, i // n
    return sum(j in mines for j in range(n * n)
               if j != i and max(abs(j % n - x), abs(j // n - y)) == 1)


def check_invariants(test, state):
    n = state.n
    opened = dict(state.opened)
    test.assertEqual(len(opened), len(state.opened))
    test.assertEqual(set(opened).intersection(state.flags), set())
    test.assertEqual(set(opened).intersection(state.mines), set())
    test.assertTrue(set(opened) <= set(range(n * n)))
    test.assertTrue(state.flags <= set(range(n * n)))
    test.assertEqual(state.opened, tuple(sorted(state.opened)))
    for i, clue in opened.items():
        test.assertEqual(clue, independent_clue(n, state.mines, i))
    if state.phase == "Won":
        test.assertEqual(set(opened), set(range(n * n)) - state.mines)
    elif state.phase == "Playing":
        test.assertLess(len(opened), n * n - len(state.mines))
    public = board.public_view(state)
    test.assertFalse(hasattr(public, "mines"))
    test.assertEqual(public.mine_count, len(state.mines))
    test.assertEqual(public.opened, state.opened)
    test.assertEqual(public.flags, state.flags)
    test.assertEqual(public.phase, state.phase)


class NxNGameInvariants(unittest.TestCase):
    def test_size_bound_matches_bend_geometry(self):
        for invalid in (0, 1, 101, 1024, -1, False, True, 10.0):
            with self.subTest(n=invalid):
                for operation in (
                    lambda: board.new_game(invalid, frozenset()),
                    lambda: board.index(invalid, 0, 0),
                    lambda: board.neighbors(invalid, 0),
                    lambda: board.storage_depth(invalid),
                ):
                    with self.assertRaises(ValueError):
                        operation()
        self.assertEqual(board.storage_depth(100), 14)
        self.assertEqual(board.index(100, 99, 99), 9999)

    def test_all_two_by_two_first_clicks_and_relocations(self):
        # Every valid mine mask (15) and every first click (4): 60 cases.
        for mask in range(15):
            mines = frozenset(i for i in range(4) if mask & (1 << i))
            for first in range(4):
                with self.subTest(mask=mask, first=first):
                    initial = board.new_game(2, mines)
                    self.assertIs(board.mark(initial, first), initial)
                    state = board.click(initial, first)
                    self.assertEqual(len(state.mines), len(mines))
                    if first in mines:
                        destination = min(set(range(4)) - mines)
                        self.assertEqual(state.mines,
                                         (mines - {first}) | {destination})
                    else:
                        self.assertEqual(state.mines, mines)
                    self.assertIn(first, dict(state.opened))
                    self.assertNotIn(first, state.mines)
                    check_invariants(self, state)
                    for i in range(4):
                        before = state
                        flagged = board.mark(before, i)
                        check_invariants(self, flagged)
                        if i in dict(before.opened) or before.phase != "Playing":
                            self.assertEqual(flagged, before)
                        else:
                            self.assertIn(i, flagged.flags)
                            self.assertIs(board.click(flagged, i), flagged)
                            self.assertEqual(board.mark(flagged, i), before)
                        after = board.click(before, i)
                        check_invariants(self, after)
                        self.assertTrue(set(dict(before.opened)) <=
                                        set(dict(after.opened)))
                        if before.phase in ("Won", "Lost"):
                            self.assertIs(after, before)

    def test_random_ten_by_ten_action_sequences(self):
        rng = random.Random(20261019)
        # 40 deterministic games, 150 actions each, including invalid inputs.
        for seed in range(40):
            mines = frozenset(rng.sample(range(100), rng.randrange(0, 31)))
            state = board.new_game(10, mines)
            for step in range(150):
                before = state
                index = rng.choice((-1, 100, 127, False, True, "3",
                                    rng.randrange(100)))
                state = (board.click(before, index) if rng.randrange(2)
                         else board.mark(before, index))
                check_invariants(self, state)
                self.assertEqual(len(state.mines), len(mines))
                self.assertTrue(set(dict(before.opened)) <=
                                set(dict(state.opened)))
                if before.phase in ("Won", "Lost"):
                    self.assertIs(state, before)
                if type(index) is not int or not 0 <= index < 100:
                    self.assertIs(state, before)

    def test_first_safe_click_keeps_mines_and_terminal_is_absorbing(self):
        mines = frozenset({0, 11, 99})
        initial = board.new_game(10, mines)
        safe = board.click(initial, 50)
        self.assertEqual(safe.mines, mines)
        check_invariants(self, safe)
        # Mine click after the first move loses and freezes both operations.
        lost = board.click(safe, 0)
        self.assertEqual(lost.phase, "Lost")
        check_invariants(self, lost)
        for i in (0, 50, 99, -1, 127):
            self.assertIs(board.click(lost, i), lost)
            self.assertIs(board.mark(lost, i), lost)


if __name__ == "__main__":
    unittest.main()
