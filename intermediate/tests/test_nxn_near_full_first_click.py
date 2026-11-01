"""N×N first-click relocation at every supported size, including word padding.

This checks *Python* packed-word and game reference implementations only.
It is not a Bend runtime test, proof, GUI test, or no-guess guarantee.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_board_oracle as game
import nxn_word_storage as words


class NearFullFirstClick(unittest.TestCase):
    def test_single_free_cell_at_both_ends_for_every_size(self):
        for n in range(2, 101):
            cells = n * n
            for free, clicked in ((cells - 1, 0), (0, cells - 1)):
                with self.subTest(n=n, free=free, clicked=clicked):
                    mines = frozenset(range(cells)) - {free}
                    original = words.pack(n, mines)
                    moved = words.relocate_first_click(n, original, clicked)
                    expected = (mines - {clicked}) | {free}
                    self.assertEqual(words.unpack(n, moved), expected)
                    self.assertEqual(words.count(n, moved), cells - 1)
                    self.assertFalse(words.has(n, moved, clicked))
                    self.assertEqual(words.unpack(n, original), mines)
                    self.assertEqual(len(moved), (cells + 31) // 32)
                    if cells % 32:
                        self.assertEqual(moved[-1] >> (cells % 32), 0)
                    actual = game.click(game.new_game(n, mines), clicked)
                    self.assertEqual(actual.mines, expected)
                    self.assertEqual(actual.opened[0][0], clicked)
                    self.assertEqual(actual.phase, "Won")
                    self.assertIs(game.click(actual, free), actual)
                    self.assertIs(game.mark(actual, clicked), actual)
                    public = game.public_view(actual)
                    self.assertEqual(public.mine_count, cells - 1)
                    self.assertFalse(hasattr(public, "mines"))

    def test_safe_single_free_cell_keeps_original_storage(self):
        for n in range(2, 101):
            cells = n * n
            free = cells // 2
            mines = frozenset(range(cells)) - {free}
            original = words.pack(n, mines)
            self.assertIs(words.relocate_first_click(n, original, free), original)
            state = game.click(game.new_game(n, mines), free)
            self.assertEqual(state.mines, mines)
            self.assertEqual(state.phase, "Won")
            self.assertEqual(state.opened[0][0], free)


if __name__ == "__main__":
    unittest.main()
