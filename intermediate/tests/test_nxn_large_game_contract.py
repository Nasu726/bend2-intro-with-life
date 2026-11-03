"""Concrete N x N game acceptance traces for a future Bend state machine.

These are finite Python reference checks, NOT tests of a Bend game engine.
They pin down observable behavior at N=10 and N=100 before porting it.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_board_oracle as Game


class NxNLargeGameContract(unittest.TestCase):
    def test_ten_by_ten_first_click_relocation_and_flag_protection(self):
        initial = Game.new_game(10, frozenset({0, 99}))
        self.assertIs(Game.mark(initial, 99), initial)  # Fresh: no flags.
        state = Game.click(initial, 0)
        self.assertEqual(state.phase, "Playing")
        self.assertEqual(state.mines, frozenset({1, 99}))
        self.assertEqual(state.opened, ((0, 1),))
        self.assertEqual(Game.public_view(state).mine_count, 2)
        marked = Game.mark(state, 99)
        self.assertEqual(marked.flags, frozenset({99}))
        self.assertIs(Game.click(marked, 99), marked)
        unmarked = Game.mark(marked, 99)
        self.assertEqual(unmarked.flags, frozenset())
        lost = Game.click(unmarked, 99)
        self.assertEqual(lost.phase, "Lost")
        self.assertIs(Game.click(lost, 2), lost)
        self.assertIs(Game.mark(lost, 1), lost)

    def test_ten_by_ten_padding_is_not_a_clickable_cell(self):
        state = Game.click(Game.new_game(10, frozenset({0, 99})), 0)
        for index in (100, 101, 127, 128, 2**32 - 1, -1, False, True):
            with self.subTest(index=index):
                self.assertIs(Game.click(state, index), state)
                self.assertIs(Game.mark(state, index), state)
        self.assertEqual(len(Game.public_view(state).opened), 1)

    def test_hundred_by_hundred_first_click_and_far_mine(self):
        state = Game.click(Game.new_game(100, frozenset({0, 9999})), 0)
        self.assertEqual(state.phase, "Playing")
        self.assertEqual(state.mines, frozenset({1, 9999}))
        self.assertEqual(state.opened, ((0, 1),))
        self.assertIs(Game.click(state, 10000), state)
        self.assertIs(Game.mark(state, 16383), state)
        self.assertEqual(Game.click(state, 9999).phase, "Lost")

    def test_zero_mine_flood_reaches_victory_and_freezes(self):
        for n in (10, 17, 100):
            with self.subTest(n=n):
                state = Game.click(Game.new_game(n, frozenset()), n + 1)
                self.assertEqual(state.phase, "Won")
                self.assertEqual(len(state.opened), n*n)
                self.assertEqual({clue for _, clue in state.opened}, {0})
                self.assertEqual(state.mines, frozenset())
                self.assertIs(Game.click(state, 0), state)
                self.assertIs(Game.mark(state, 0), state)

    def test_non_toroidal_row_boundary(self):
        state = Game.click(Game.new_game(10, frozenset({9})), 10)
        self.assertEqual(dict(state.opened)[10], 0)
        self.assertEqual(state.phase, "Won")
        self.assertEqual(len(state.opened), 99)
        self.assertNotIn(9, dict(state.opened))


if __name__ == "__main__":
    unittest.main()
