"""Every supported N (2..100): packed-word boundaries and first-click contract.

Finite Python-only verification. This does NOT test Bend's implementation,
its Array representation, the GUI, or no-guess generation.
"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_word_storage as words


class AllSizesPackedStorage(unittest.TestCase):
    def test_every_size_and_last_word_padding(self):
        for n in range(2, 101):
            cells = n * n
            length = (cells + 31) // 32
            last = cells - 1
            with self.subTest(n=n):
                empty = words.pack(n, ())
                self.assertEqual(len(empty), length)
                self.assertEqual(words.count(n, empty), 0)
                # Check the first and last cell, and both sides of every
                # 32-bit word boundary. This is not a full-board enumeration.
                indices = {0, 1, last, last - 1}
                for boundary in range(32, cells, 32):
                    indices.update((boundary - 1, boundary))
                current = empty
                for i in sorted(indices):
                    previous = current
                    current = words.set_cell(n, current, i, True)
                    self.assertFalse(words.has(n, previous, i))
                    self.assertTrue(words.has(n, current, i))
                self.assertEqual(words.unpack(n, current), indices)
                self.assertEqual(words.count(n, current), len(indices))
                # Padding bits beyond the logical board must remain zero.
                padding = length * 32 - cells
                if padding:
                    self.assertEqual(current[-1] >> (32 - padding), 0)
                    with self.assertRaises(ValueError):
                        words.validate(n, current[:-1] +
                                       (current[-1] | (1 << (32 - padding)),))
                self.assertFalse(words.has(n, current, cells))
                self.assertFalse(words.has(n, current, 2**32 - 1))

    def test_every_size_relocation_changes_exactly_two_bits(self):
        rng = random.Random(20261021)
        for n in range(2, 101):
            cells = n * n
            # Dense, sparse and word-boundary placements, deterministic.
            candidates = (
                {0},
                {cells - 1},
                {0, cells - 1},
                {i for i in range(cells) if i % 32 in (0, 31)},
                set(rng.sample(range(cells), cells // 2)),
                set(range(cells)) - {cells - 1},
            )
            for mines in candidates:
                original = words.pack(n, mines)
                for clicked in (0, cells // 2, cells - 1):
                    with self.subTest(n=n, clicked=clicked, count=len(mines)):
                        moved = words.relocate_first_click(n, original, clicked)
                        actual = words.unpack(n, moved)
                        self.assertEqual(words.count(n, moved), len(mines))
                        self.assertNotIn(clicked, actual)
                        self.assertEqual(words.unpack(n, original), mines)
                        if clicked in mines:
                            destination = min(set(range(cells)) - mines)
                            self.assertEqual(actual ^ mines,
                                             {clicked, destination})
                        else:
                            self.assertIs(moved, original)
                            self.assertEqual(actual, mines)


if __name__ == "__main__":
    unittest.main()
