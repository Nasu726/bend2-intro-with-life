"""Exhaustive small-board and deterministic large-board relocation oracle.

Only the bit-packed Python reference is checked; not the Bend game engine.
"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_word_storage as bits


class FirstClickWordRelocation(unittest.TestCase):
    def test_all_small_board_masks_and_clicks(self):
        # 2x2: 15 masks x 4; 3x3: 511 masks x 9 = 4,659 valid cases.
        for n in (2, 3):
            for mask in range((1 << (n*n)) - 1):
                mines = frozenset(i for i in range(n*n) if mask & (1 << i))
                words = bits.pack(n, mines)
                for clicked in range(n*n):
                    with self.subTest(n=n, mask=mask, clicked=clicked):
                        actual = bits.relocate_first_click(n, words, clicked)
                        if clicked in mines:
                            replacement = min(set(range(n*n)) - mines)
                            expected = (mines - {clicked}) | {replacement}
                        else:
                            expected = mines
                            self.assertIs(actual, words)
                        self.assertEqual(bits.unpack(n, actual), expected)
                        self.assertEqual(bits.count(n, actual), len(mines))
                        self.assertFalse(bits.has(n, actual, clicked))
                        self.assertEqual(words, bits.pack(n, mines))

    def test_word_boundaries_and_random_large_boards(self):
        rng = random.Random(20261020)
        for n in (4, 10, 17, 100):
            for clicked in sorted({0, 31, 32, 63, 64, 99, n*n-1} & set(range(n*n))):
                mines = {clicked, n*n-1} if clicked != n*n-1 else {clicked}
                words = bits.pack(n, mines)
                moved = bits.relocate_first_click(n, words, clicked)
                expected = (mines - {clicked}) | {min(set(range(n*n)) - mines)}
                self.assertEqual(bits.unpack(n, moved), expected)
            for _ in range(80):
                mines = set(rng.sample(range(n*n), rng.randrange(n*n)))
                clicked = rng.randrange(n*n)
                words = bits.pack(n, mines)
                moved = bits.relocate_first_click(n, words, clicked)
                if clicked in mines:
                    mines.remove(clicked)
                    mines.add(min(set(range(n*n)) - bits.unpack(n, words)))
                self.assertEqual(bits.unpack(n, moved), mines)
                self.assertFalse(bits.has(n, moved, clicked))

    def test_invalid_click_and_full_board_rejected(self):
        for n in (2, 10, 100):
            words = bits.pack(n, {0})
            for clicked in (-1, n*n, n*n+27, True, False, 1.0, "0"):
                with self.subTest(n=n, clicked=clicked), self.assertRaises(ValueError):
                    bits.relocate_first_click(n, words, clicked)
            with self.assertRaises(ValueError):
                bits.relocate_first_click(n, bits.pack(n, range(n*n)), 0)
            with self.assertRaises(ValueError):
                bits.relocate_first_click(n, words[:-1], 0)


if __name__ == "__main__":
    unittest.main()
