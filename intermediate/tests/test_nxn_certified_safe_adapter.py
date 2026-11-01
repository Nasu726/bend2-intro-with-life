"""Independent finite checks for certified safe evidence in six-bit requests.

Certified safe cells are not revealed clues: they have no displayed number.
They must be excluded from the unknown universe without subtracting a mine.
"""
from itertools import combinations
from pathlib import Path
from random import Random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_three_clue_adapter import from_public_clues, from_public_board


def neighbors(n, index):
    x, y = index % n, index // n
    return {i for i in range(n * n) if i != index
            and abs(i % n - x) <= 1 and abs(i // n - y) <= 1}


def whole_models(n, opened, total, known_mines, known_safe):
    shown = {cell for cell, _ in opened}
    remaining = sorted(set(range(n * n)) - shown - known_mines - known_safe)
    result = []
    for extra in combinations(remaining, total - len(known_mines)):
        mines = known_mines | set(extra)
        if all(len(mines & neighbors(n, cell)) == number
               for cell, number in opened):
            result.append(mines)
    return result


def local_models(request):
    a, b, c, ra, rb, rc, total, use_total = request.bend_arguments()
    return {bits for bits in range(64)
            if all((bits & mask).bit_count() == count
                   for mask, count in zip((a, b, c), (ra, rb, rc)))
            and (not use_total or bits.bit_count() == total)}


class CertifiedSafeAdapter(unittest.TestCase):
    def test_safe_evidence_enables_exact_global_total(self):
        opened = ((0, 1), (1, 2), (7, 2))
        known_mines = (2,)
        known_safe = (8, 9, 12, 13, 14, 15)
        request = from_public_clues(
            4, opened, 3, certified_mines=known_mines,
            certified_safe=known_safe)
        self.assertIsNotNone(request)
        self.assertEqual(request.cells, (3, 4, 5, 6, 10, 11))
        self.assertEqual(request.bend_arguments(),
                         (6, 14, 57, 1, 1, 1, 2, True))
        self.assertEqual(len(local_models(request)), 6)
        self.assertEqual(len(whole_models(
            4, opened, 3, set(known_mines), set(known_safe))), 6)
        without_safe = from_public_clues(
            4, opened, 3, certified_mines=known_mines)
        self.assertFalse(without_safe.use_total)
        self.assertEqual(without_safe.total, 0)

    def test_certified_safe_frontier_is_not_zero_padded(self):
        opened = ((0, 1), (2, 1), (7, 1))
        self.assertIsNotNone(from_public_clues(3, opened, 2))
        # Five unknown cells remain, not a six-bit universe.
        self.assertIsNone(from_public_clues(
            3, opened, 2, certified_safe=(3,)))

    def test_bad_certified_safe_evidence_is_rejected(self):
        opened = ((0, 1), (1, 2), (7, 2))
        for safe in ((0,), (2,), (8, 8), (16,), (-1,),
                     (True,), (8, False)):
            with self.subTest(safe=safe):
                with self.assertRaises(ValueError):
                    from_public_clues(
                        4, opened, 3, certified_mines=(2,),
                        certified_safe=safe)
        with self.assertRaises(ValueError):
            from_public_board(
                4, opened, 3, certified_mines=(2,),
                certified_safe=None)

    def test_independent_whole_board_projection(self):
        rng = Random(20261026)
        requests_checked = 0
        for _ in range(100):
            shown = tuple(sorted(rng.sample(range(16), rng.randrange(3, 9))))
            hidden = sorted(set(range(16)) - set(shown))
            true_mines = set(rng.sample(hidden, rng.randrange(4)))
            opened = tuple((i, len(true_mines & neighbors(4, i)))
                           for i in shown)
            known_mines = set(rng.sample(
                sorted(true_mines), rng.randrange(len(true_mines) + 1)))
            available_safe = sorted(set(hidden) - true_mines)
            known_safe = set(rng.sample(
                available_safe, rng.randrange(len(available_safe) + 1)))
            requests = from_public_board(
                4, opened, len(true_mines),
                certified_mines=sorted(known_mines),
                certified_safe=sorted(known_safe))
            models = whole_models(
                4, opened, len(true_mines), known_mines, known_safe)
            self.assertTrue(models)  # The sampled true layout is a witness.
            for request in requests:
                self.assertFalse(set(request.cells) & (
                    set(shown) | known_mines | known_safe))
                self.assertEqual(
                    request.use_total,
                    len(set(range(16)) - set(shown)
                        - known_mines - known_safe) == 6)
                projected = {
                    sum(1 << bit for bit, cell in enumerate(request.cells)
                        if cell in mines) for mines in models
                }
                self.assertLessEqual(projected, local_models(request))
                requests_checked += 1
        self.assertGreater(requests_checked, 0)


if __name__ == "__main__":
    unittest.main()
