"""Check U32 word boundaries independently of the future Bend implementation."""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_word_storage as bits


class WordStorage(unittest.TestCase):
    def test_boundaries_and_padding(self):
        rng = random.Random(20261020)
        for n in (2, 3, 4, 10, 17, 100):
            for _ in range(20):
                mines = frozenset(rng.sample(range(n*n), rng.randrange(n*n+1)))
                words = bits.pack(n, mines)
                self.assertEqual(len(words), (n*n+31)//32)
                self.assertEqual(bits.unpack(n, words), mines)
                self.assertEqual(bits.count(n, words), len(mines))
                for i in (n*n, n*n+1, len(words)*32-1, 4294967295):
                    self.assertFalse(bits.has(n, words, i))
        for i in (31, 32, 63, 64, 99):
            self.assertTrue(bits.has(10, bits.pack(10, {i}), i))

    def test_invalid_inputs(self):
        for n, mines in ((1, ()), (101, ()), (10, (100,)),
                         (10, (True,)), (10, None), (True, ())):
            with self.subTest(n=n, mines=mines), self.assertRaises(ValueError):
                bits.pack(n, mines)

    def test_exhaustive_small_boards(self):
        for n in (2, 3):
            for mask in range(1 << (n*n)):
                mines = {i for i in range(n*n) if mask & (1 << i)}
                words = bits.pack(n, mines)
                with self.subTest(n=n, mask=mask):
                    self.assertEqual(bits.unpack(n, words), mines)
                    self.assertEqual(bits.count(n, words), len(mines))
                    self.assertEqual(bits.pack(n, list(mines) + list(mines)), words)
                    for i in range(n*n):
                        self.assertEqual(bits.has(n, words, i), i in mines)

    def test_mutations_are_pure_and_cross_word(self):
        for n in (4, 10, 100):
            cells = n*n
            original = bits.pack(n, ())
            current = original
            indices = sorted({0, 15, 16, 31, 32, 63, 64, 99,
                              cells-1} & set(range(cells)))
            for i in indices:
                updated = bits.set_cell(n, current, i, True)
                self.assertFalse(bits.has(n, current, i))
                self.assertTrue(bits.has(n, updated, i))
                self.assertEqual(bits.set_cell(n, updated, i, True), updated)
                current = updated
            self.assertEqual(bits.unpack(n, current), frozenset(indices))
            self.assertEqual(bits.count(n, current), len(indices))
            for i in reversed(indices):
                current = bits.set_cell(n, current, i, False)
                self.assertFalse(bits.has(n, current, i))
            self.assertEqual(current, original)

    def test_invalid_storage_and_padding_are_rejected(self):
        good = bits.pack(10, {0, 31, 32, 99})
        bad = (good[:-1], good + (0,), list(good),
               good[:-1] + (1 << 4,),
               (True,) + good[1:], (-1,) + good[1:],
               (1 << 32,) + good[1:], ("1",) + good[1:])
        for words in bad:
            with self.subTest(words=words):
                for action in (lambda: bits.validate(10, words),
                               lambda: bits.unpack(10, words),
                               lambda: bits.count(10, words),
                               lambda: bits.has(10, words, 0),
                               lambda: bits.set_cell(10, words, 0, True)):
                    with self.assertRaises(ValueError):
                        action()
        for i in (-1, 100, 127, True, False, 1.0):
            with self.subTest(i=i), self.assertRaises(ValueError):
                bits.set_cell(10, good, i, True)
        for value in (0, 1, None, "true"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bits.set_cell(10, good, 0, value)
        self.assertFalse(bits.has(10, good, 127))
        self.assertFalse(bits.has(10, good, True))

    def test_random_mutations_match_set_reference(self):
        rng = random.Random(20261020)
        for n in (2, 3, 4, 10, 17, 100):
            words = bits.pack(n, ())
            reference = set()
            for _ in range(150):
                i = rng.randrange(n*n)
                value = bool(rng.randrange(2))
                words = bits.set_cell(n, words, i, value)
                if value:
                    reference.add(i)
                else:
                    reference.discard(i)
                self.assertEqual(bits.count(n, words), len(reference))
                self.assertEqual(bits.unpack(n, words), reference)


if __name__ == "__main__":
    unittest.main()
