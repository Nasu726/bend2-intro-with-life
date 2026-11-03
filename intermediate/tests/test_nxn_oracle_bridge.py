"""Cross-check two independent N x N Python models at the first-click boundary.

The packed-word oracle and the game-state oracle are separate implementations.
This verifies their integration contract, not the Bend engine or no-guess mode.
"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_board_oracle as game
import nxn_word_storage as words


def independent_clue(n, mines, i):
    x, y = i % n, i // n
    return sum(j in mines for j in range(n * n)
               if j != i and max(abs(j % n - x), abs(j // n - y)) == 1)


class PackedWordsGameBridge(unittest.TestCase):
    def check_first_click(self, n, mines, first):
        initial = game.new_game(n, mines)
        packed = words.pack(n, mines)
        expected = words.relocate_first_click(n, packed, first)
        actual = game.click(initial, first)
        self.assertEqual(actual.mines, words.unpack(n, expected))
        self.assertEqual(len(actual.mines), len(mines))
        self.assertNotIn(first, actual.mines)
        self.assertIn(first, dict(actual.opened))
        self.assertEqual(words.pack(n, actual.mines), expected)
        self.assertEqual(initial.mines, mines)
        self.assertEqual(words.unpack(n, packed), mines)
        self.assertEqual(actual.flags, frozenset())
        self.assertIn(actual.phase, ("Playing", "Won"))
        for cell, value in actual.opened:
            self.assertFalse(words.has(n, expected, cell))
            self.assertEqual(value, independent_clue(n, actual.mines, cell))
        public = game.public_view(actual)
        self.assertFalse(hasattr(public, "mines"))
        self.assertEqual(public.mine_count, words.count(n, expected))
        self.assertEqual(public.opened, actual.opened)

    def test_exhaustive_small_first_clicks(self):
        # All non-full 2x2 and 3x3 masks: 60 + 4599 = 4659 first clicks.
        for n in (2, 3):
            for mask in range((1 << (n * n)) - 1):
                mines = frozenset(i for i in range(n * n) if mask >> i & 1)
                for first in range(n * n):
                    with self.subTest(n=n, mask=mask, first=first):
                        self.check_first_click(n, mines, first)

    def test_cross_word_and_large_boards(self):
        rng = random.Random(20261020)
        for n in (4, 10, 17, 100):
            for first in sorted({0, 31, 32, 63, 64, 99, n * n - 1}
                                & set(range(n * n))):
                background = ({i for i in range(n * n)
                               if i % 3 == 0 and i != first}
                              if n >= 17 else set())
                self.check_first_click(n, frozenset({first} | background), first)
            for _ in range(20):
                count = rng.randrange(max(1, n * n // 4), n * n)
                mines = frozenset(rng.sample(range(n * n), count))
                first = rng.randrange(n * n)
                self.check_first_click(n, mines, first)

    def test_reject_full_board_and_invalid_size(self):
        for n in (2, 3, 10, 100):
            with self.assertRaises(ValueError):
                game.new_game(n, frozenset(range(n * n)))
            with self.assertRaises(ValueError):
                words.relocate_first_click(n, words.pack(n, range(n * n)), 0)
        for n in (0, 1, 101, True, False, 10.0):
            with self.assertRaises(ValueError):
                game.new_game(n, frozenset())
            with self.assertRaises(ValueError):
                words.pack(n, ())


if __name__ == "__main__":
    unittest.main()
