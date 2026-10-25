"""Finite independent checks for public-board -> Bend six-bit inputs."""
from itertools import combinations
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_three_clue_adapter import from_public_clues


def neighbors(n, index):
    x, y = index % n, index // n
    return {other for other in range(n*n)
            if other != index and abs(other % n - x) <= 1
            and abs(other // n - y) <= 1}


def local_models(item):
    a, b, c, ra, rb, rc, total, use_total = item.bend_arguments()
    return tuple(bits for bits in range(64)
                 if all((bits & mask).bit_count() == number
                        for mask, number in zip((a, b, c), (ra, rb, rc)))
                 and (not use_total or bits.bit_count() == total))


def whole_models(n, opened, mine_count):
    shown = {cell for cell, _ in opened}
    hidden = tuple(sorted(set(range(n*n)) - shown))
    models = []
    for count in range(len(hidden)+1) if mine_count is None else (mine_count,):
        for mines in combinations(hidden, count):
            mine_set = set(mines)
            if all(len(mine_set & neighbors(n, cell)) == clue
                   for cell, clue in opened):
                models.append(mine_set)
    return models


class PublicThreeAdapter(unittest.TestCase):
    def test_named_lesson_and_global_total(self):
        clues = ((0, 1), (2, 1), (7, 1))
        actual = from_public_clues(3, clues, 2)
        self.assertEqual(actual.cells, (1, 3, 4, 5, 6, 8))
        self.assertEqual(actual.bend_arguments(),
                         (7, 13, 62, 1, 1, 1, 2, True))
        self.assertEqual(local_models(actual), (17, 33))
        without = from_public_clues(3, clues)
        self.assertEqual(without.bend_arguments(),
                         (7, 13, 62, 1, 1, 1, 0, False))
        self.assertEqual(len(local_models(without)), 3)

    def test_all_3x3_three_clue_geometries_and_all_mine_layouts(self):
        # Every three-open-cell geometry and all 2^6 hidden mine layouts.
        # Supported geometries have six distinct frontier cells, so the
        # kernel models and whole-board models must agree exactly.
        checked = 0
        for shown in combinations(range(9), 3):
            hidden = tuple(sorted(set(range(9)) - set(shown)))
            for assignment in range(64):
                mines = {cell for bit, cell in enumerate(hidden)
                         if assignment & (1 << bit)}
                opened = tuple((cell, len(mines & neighbors(3, cell)))
                               for cell in shown)
                for total in (None, len(mines)):
                    actual = from_public_clues(3, opened, total)
                    if actual is None:
                        continue
                    local = {frozenset(actual.cells[bit] for bit in range(6)
                                       if bits & (1 << bit))
                             for bits in local_models(actual)}
                    whole = {frozenset(m) for m in whole_models(3, opened, total)}
                    self.assertEqual(local, whole, (shown, assignment, total))
                    checked += 1
        self.assertEqual(checked, 48 * 64 * 2)

    def test_outside_unknowns_never_count_as_zero_mines(self):
        # N=4 has 13 hidden cells but only six frontier cells.  Even with
        # a public global total, the kernel must ignore it, not claim all
        # those mines are inside its six-bit frontier.
        opened = ((0, 1), (1, 1), (5, 1))
        actual = from_public_clues(4, opened, 2)
        self.assertEqual(len(actual.cells), 6)
        self.assertFalse(actual.use_total)
        self.assertEqual(actual.total, 0)
        local = local_models(actual)
        whole = whole_models(4, opened, 2)
        self.assertTrue(whole)
        projected = {sum(1 << bit for bit, cell in enumerate(actual.cells)
                         if cell in mines) for mines in whole}
        self.assertLessEqual(projected, set(local))

    def test_rejects_non_six_bit_frontiers_without_padding(self):
        self.assertIsNone(from_public_clues(2, ((0, 1), (1, 1), (2, 1)), 1))
        self.assertIsNone(from_public_clues(4, ((0, 1), (3, 1), (12, 1)), 2))

    def test_malformed_public_inputs(self):
        bad = [(True, ((0, 1), (2, 1), (7, 1)), 2),
               (3, ((0, 1), (0, 1), (7, 1)), 2),
               (3, ((0, 1), (2, 1)), 2),
               (3, ((0, True), (2, 1), (7, 1)), 2),
               (3, ((0, 1), (2, 1), (9, 1)), 2),
               (3, ((0, 1), (2, 1), (7, 1)), True),
               (3, ((0, 1), (2, 1), (7, 1)), 7)]
        for n, clues, total in bad:
            with self.subTest(n=n, clues=clues, total=total):
                with self.assertRaises(ValueError):
                    from_public_clues(n, clues, total)


if __name__ == "__main__":
    unittest.main()
