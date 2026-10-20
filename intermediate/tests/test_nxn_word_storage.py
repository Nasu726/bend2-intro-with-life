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
                for i in (n*n, n*n+1, len(words)*32-1, 4294967295):
                    self.assertFalse(bits.has(n, words, i))
        for i in (31, 32, 63, 64, 99):
            self.assertTrue(bits.has(10, bits.pack(10, {i}), i))

    def test_invalid_inputs(self):
        for n, mines in ((1, ()), (101, ()), (10, (100,)), (10, (True,))):
            with self.assertRaises(ValueError):
                bits.pack(n, mines)


if __name__ == "__main__":
    unittest.main()
