"""Finite cross-model check of published clues through game transitions.

The bit-packed clue implementation and the state-machine oracle are separate
Python references.  This does NOT execute Bend or prove N x N correctness.
"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_board_oracle as game
import nxn_word_storage as words


def direct_clue(n, mines, i):
    """Independent set-and-coordinate calculation, without either oracle API."""
    x, y = i % n, i // n
    return sum((y + dy) * n + (x + dx) in mines
               for dy in (-1, 0, 1) for dx in (-1, 0, 1)
               if (dx or dy) and 0 <= x + dx < n and 0 <= y + dy < n)


class ClueStateBridge(unittest.TestCase):
    def check_state(self, state, initial_count):
        n = state.n
        packed = words.pack(n, state.mines)
        self.assertEqual(words.count(n, packed), initial_count)
        self.assertEqual(words.unpack(n, packed), state.mines)
        opened = dict(state.opened)
        self.assertEqual(len(opened), len(state.opened))
        self.assertTrue(opened.keys().isdisjoint(state.flags))
        self.assertTrue(opened.keys().isdisjoint(state.mines))
        public = game.public_view(state)
        self.assertFalse(hasattr(public, "mines"))
        self.assertEqual(public.mine_count, initial_count)
        self.assertEqual(public.opened, state.opened)
        self.assertEqual(public.flags, state.flags)
        for i, shown in state.opened:
            self.assertEqual(shown, words.adjacent_count(n, packed, i),
                             (n, i, state.phase))
            self.assertEqual(shown, direct_clue(n, state.mines, i))
        if state.phase == "Won":
            self.assertEqual(len(opened), n * n - initial_count)
        elif state.phase == "Playing":
            self.assertLess(len(opened), n * n - initial_count)

    def test_every_small_first_click_and_followup(self):
        # 2x2: 15*4*4; 3x3: 511*9*9 = 41,391 follow-up clicks.
        for n in (2, 3):
            for mask in range((1 << (n * n)) - 1):
                mines = frozenset(i for i in range(n * n) if mask >> i & 1)
                initial = game.new_game(n, mines)
                for first in range(n * n):
                    state = game.click(initial, first)
                    self.check_state(state, len(mines))
                    for second in range(n * n):
                        after = game.click(state, second)
                        self.check_state(after, len(mines))
                        # Flagging must never change any already shown clue.
                        flagged = game.mark(state, second)
                        self.check_state(flagged, len(mines))
                        self.check_state(game.click(flagged, second), len(mines))

    def test_all_sizes_corner_word_edge_and_random_sequences(self):
        rng = random.Random(20261021)
        for n in range(2, 101):
            cells = n * n
            mines = frozenset(rng.sample(range(cells), cells // 4))
            state = game.new_game(n, mines)
            self.check_state(state, len(mines))
            indices = [0, n - 1, n, cells - 1, 31, 32, 63, 64, 99]
            valid = [i for i in indices if i < cells]
            state = game.click(state, rng.choice(valid))
            self.check_state(state, len(mines))
            for _ in range(20):
                i = rng.choice(valid) if rng.randrange(2) else rng.randrange(cells)
                state = game.mark(state, i) if rng.randrange(3) == 0 else game.click(state, i)
                self.check_state(state, len(mines))


if __name__ == "__main__":
    unittest.main()
