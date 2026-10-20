"""Check that first-click mine relocation preserves the N x N clue contract.

This is an independent Python reference-model test, not Bend typechecking,
not a proof for all board sizes, and not a no-guess solver test.  The test
recomputes clues from a plain set rather than trusting the packed words.
"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_word_storage as bits


def neighbors(n, cell):
    """Independent non-toroidal, row-major eight-neighborhood."""
    x, y = cell % n, cell // n
    return frozenset(v*n + u for v in range(max(0, y-1), min(n, y+2))
                     for u in range(max(0, x-1), min(n, x+2))
                     if (u, v) != (x, y))


def clue(n, mines, cell):
    return len(neighbors(n, cell) & mines)


class RelocationClueContract(unittest.TestCase):
    def check_case(self, n, mines, clicked):
        old = bits.pack(n, mines)
        updated = bits.relocate_first_click(n, old, clicked)
        after = bits.unpack(n, updated)
        self.assertEqual(bits.unpack(n, old), mines, "original must be unchanged")
        self.assertFalse(bits.has(n, updated, clicked))
        self.assertEqual(len(after), len(mines))
        if clicked not in mines:
            self.assertIs(updated, old)
            self.assertEqual(after, mines)
            return
        replacement = min(set(range(n*n)) - mines)
        self.assertEqual(after, (mines - {clicked}) | {replacement})
        self.assertEqual(mines ^ after, {clicked, replacement})
        changed_words = {i for i, (a, b) in enumerate(zip(old, updated)) if a != b}
        self.assertEqual(changed_words, {clicked // 32, replacement // 32})
        # Only neighbors of the removed/added mine can have different clues.
        affected = neighbors(n, clicked) | neighbors(n, replacement)
        for cell in range(n*n):
            before_clue = clue(n, mines, cell)
            after_clue = clue(n, after, cell)
            self.assertEqual(after_clue, before_clue
                             - int(cell in neighbors(n, clicked))
                             + int(cell in neighbors(n, replacement)))
            if cell not in affected:
                self.assertEqual(before_clue, after_clue)
            self.assertLessEqual(after_clue, 8)

    def test_exhaustive_two_by_two_and_three_by_three(self):
        for n in (2, 3):
            for mask in range((1 << (n*n)) - 1):
                mines = frozenset(i for i in range(n*n) if mask & (1 << i))
                for clicked in range(n*n):
                    with self.subTest(n=n, mask=mask, clicked=clicked):
                        self.check_case(n, mines, clicked)

    def test_cross_word_boundaries_and_large_boards(self):
        rng = random.Random(20261020)
        for n in (4, 10, 17, 100):
            boundary = sorted({0, 1, 30, 31, 32, 33, 63, 64, 99, n*n-1}
                              & set(range(n*n)))
            for clicked in boundary:
                self.check_case(n, frozenset({clicked, n*n-1}), clicked)
            for _ in range(12):
                mines = frozenset(rng.sample(range(n*n), rng.randrange(n*n)))
                self.check_case(n, mines, rng.randrange(n*n))

    def test_full_board_is_rejected_before_clues(self):
        for n in (2, 3, 10):
            with self.assertRaises(ValueError):
                bits.relocate_first_click(n, bits.pack(n, range(n*n)), 0)


if __name__ == "__main__":
    unittest.main()
