"""Certified public mines: residual clues and global budget stay sound.

This is a finite Python reference check, not a proof that a player's flags
are correct or that Bend has an automatic certified-mine extractor.
"""
from itertools import combinations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
from nxn_three_clue_adapter import from_public_board, from_public_clues


def neighbors(n, i):
    return {j for j in range(n*n) if j != i
            and abs(j % n - i % n) <= 1 and abs(j // n - i // n) <= 1}


def local_models(request):
    a, b, c, ra, rb, rc, total, use_total = request.bend_arguments()
    return {bits for bits in range(64)
            if all((bits & mask).bit_count() == number
                   for mask, number in zip((a, b, c), (ra, rb, rc)))
            and (not use_total or bits.bit_count() == total)}


def global_models(n, opened, mine_count, certified):
    unknown = sorted(set(range(n*n)) - {c for c, _ in opened} - set(certified))
    count = mine_count - len(certified)
    return [set(assignment) | set(certified)
            for assignment in combinations(unknown, count)
            if all(len((set(assignment) | set(certified)) & neighbors(n, i)) == clue
                   for i, clue in opened)]


class CertifiedResiduals(unittest.TestCase):
    def test_residual_example_and_local_budget_guard(self):
        clues = ((0, 1), (1, 2), (7, 2))
        self.assertEqual(from_public_board(4, clues, 3), ())
        requests = from_public_board(4, clues, 3, certified_mines=(2,))
        self.assertEqual(len(requests), 1)
        request = requests[0]
        self.assertEqual(request.cells, (3, 4, 5, 6, 10, 11))
        self.assertEqual(request.masks, (6, 14, 57))
        self.assertEqual(request.counts, (1, 1, 1))
        self.assertEqual((request.total, request.use_total), (0, False))
        self.assertEqual(from_public_clues(
            4, clues, 3, certified_mines=(2,)), request)
        models = global_models(4, clues, 3, {2})
        self.assertTrue(models)
        projections = {sum(1 << bit for bit, cell in enumerate(request.cells)
                           if cell in mines) for mines in models}
        self.assertLessEqual(projections, local_models(request))

    def test_global_budget_subtracts_certified_mines(self):
        mines = {2, 4, 11}  # Used by the independent oracle only.
        shown = (0, 1, 7, 8, 9, 12, 13, 14, 15)
        clues = tuple((cell, len(neighbors(4, cell) & mines))
                      for cell in shown)
        requests = from_public_board(4, clues, 3, certified_mines=(2,))
        self.assertTrue(requests)
        self.assertTrue(all(r.use_total and r.total == 2 for r in requests))
        self.assertTrue(all(r.cells == (3, 4, 5, 6, 10, 11)
                            for r in requests))
        models = global_models(4, clues, 3, {2})
        self.assertTrue(models)
        for request in requests:
            projections = {
                sum(1 << bit for bit, cell in enumerate(request.cells)
                    if cell in mines) for mines in models}
            self.assertLessEqual(projections, local_models(request))

    def test_invalid_certification_is_rejected(self):
        clues = ((0, 1), (1, 2), (7, 2))
        for certified in ((0,), (16,), (-1,), (2, 2), (True,),
                          (2.0,), ([2],), "2"):
            with self.subTest(certified=certified), self.assertRaises(ValueError):
                from_public_board(4, clues, 3, certified_mines=certified)
        for total in (0, 17, True):
            with self.subTest(total=total), self.assertRaises(ValueError):
                from_public_board(4, clues, total, certified_mines=(2,))
        with self.assertRaises(ValueError):
            from_public_board(4, ((0, 1), (1, 0), (7, 2)),
                              3, certified_mines=(2,))

    def test_all_66_two_mine_unknown_assignments(self):
        shown = (0, 1, 7)
        known = 2
        unknown = tuple(sorted(set(range(16)) - set(shown) - {known}))
        checked = 0
        for subset in combinations(unknown, 2):
            mines = set(subset) | {known}
            clues = tuple((cell, len(neighbors(4, cell) & mines))
                          for cell in shown)
            requests = from_public_board(
                4, clues, 3, certified_mines=(known,))
            self.assertEqual(len(requests), 1)
            request = requests[0]
            models = global_models(4, clues, 3, {known})
            projections = {
                sum(1 << bit for bit, cell in enumerate(request.cells)
                    if cell in model) for model in models}
            self.assertLessEqual(projections, local_models(request))
            checked += 1
        self.assertEqual(checked, 66)


if __name__ == "__main__":
    unittest.main()
