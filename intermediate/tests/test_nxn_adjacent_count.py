"""Finite Python reference checks for N x N non-wrapping clue counts.

These tests do not execute Bend, establish universal laws, or test GUI input.
"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_word_storage as bits


def expected(n, mines, i):
    """Independent set-based oracle, without packed-word operations."""
    x, y = i % n, i // n
    return sum(j in mines for j in range(n*n)
               if j != i and max(abs(j % n-x), abs(j//n-y)) == 1)


class AdjacentCount(unittest.TestCase):
    def test_exhaustive_small_boards(self):
        for n in (2, 3):
            for mask in range(1 << (n*n)):
                mines = frozenset(i for i in range(n*n) if mask & (1 << i))
                words = bits.pack(n, mines)
                for i in range(n*n):
                    self.assertEqual(bits.adjacent_count(n, words, i),
                                     expected(n, mines, i), (n, mask, i))

    def test_all_sizes_and_word_boundaries(self):
        rng = random.Random(20261021)
        for n in range(2, 101):
            cells = n*n
            mines = frozenset(rng.sample(range(cells), cells//3))
            words = bits.pack(n, mines)
            indices = {0, n-1, n, cells//2, cells-1, 31, 32, 63, 64, 99}
            indices = sorted(i for i in indices if i < cells)
            for i in indices:
                with self.subTest(n=n, i=i):
                    self.assertEqual(bits.adjacent_count(n, words, i),
                                     expected(n, mines, i))
                    self.assertEqual(bits.adjacent_count(n, bits.pack(n, ()), i), 0)
                    self.assertEqual(bits.adjacent_count(n, bits.pack(n, range(cells)), i),
                                     expected(n, frozenset(range(cells)), i))

    def test_toggle_locality(self):
        for n in (2, 10, 100):
            cells = n*n
            positions = sorted({0, 1, n-1, n, n+1, 31, 32, 63, 64, 99, cells-1}
                               & set(range(cells)))
            empty = bits.pack(n, ())
            for i in positions:
                for j in positions:
                    words = bits.pack(n, (j,))
                    self.assertEqual(bits.adjacent_count(n, words, i),
                                     int(j != i and max(abs(i % n-j % n),
                                                        abs(i//n-j//n)) == 1))
                    self.assertEqual(bits.adjacent_count(n, empty, i), 0)

    def test_invalid_index_and_storage(self):
        words = bits.pack(10, (0, 31, 32, 99))
        for i in (-1, 100, 127, 2**32-1, True, 1.0):
            with self.subTest(i=i), self.assertRaises(ValueError):
                bits.adjacent_count(10, words, i)
        for n, packed in ((1, words), (101, words), (10, words[:-1]),
                          (10, words[:-1]+(1 << 30,))):
            with self.subTest(n=n), self.assertRaises(ValueError):
                bits.adjacent_count(n, packed, 0)


if __name__ == "__main__":
    unittest.main()
