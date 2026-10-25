"""Finite independent checks for public-board -> Bend six-bit inputs."""
from itertools import combinations
from random import Random
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_three_clue_adapter import (from_public_clues, from_public_board,
                                    combine_public_decisions)


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



def summarize_local(item):
    models = local_models(item)
    if not models:
        return None
    union, common = 0, 63
    for bits in models:
        union |= bits
        common &= bits
    return (63 & ~union, common, len(models))


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


    def assert_sound_public_board(self, n, opened, total):
        requests = from_public_board(n, opened, total)
        models = whole_models(n, opened, total)
        self.assertTrue(models)
        decision = combine_public_decisions(
            (request, summarize_local(request)) for request in requests)
        self.assertIsNotNone(decision)
        safe, mines = map(set, decision)
        hidden = set(range(n * n)) - {cell for cell, _ in opened}
        forced_safe = hidden - set.union(*models)
        forced_mines = set.intersection(*models)
        self.assertLessEqual(safe, forced_safe)
        self.assertLessEqual(mines, forced_mines)
        for request in requests:
            projected = {
                sum(1 << bit for bit, cell in enumerate(request.cells)
                    if cell in model)
                for model in models
            }
            self.assertLessEqual(projected, set(local_models(request)))

    def test_three_clues_match_single_request(self):
        clues = ((0, 1), (2, 1), (7, 1))
        self.assertEqual(from_public_board(3, clues, 2),
                         (from_public_clues(3, clues, 2),))

    def test_four_public_clues_exclude_all_revealed_cells(self):
        opened = ((0, 0), (1, 0), (2, 1), (4, 1))
        requests = from_public_board(4, opened, 2)
        self.assertEqual(len(requests), 2)
        self.assertEqual([r.cells for r in requests],
                         [(3, 5, 6, 7, 8, 9)] * 2)
        self.assertEqual([r.masks for r in requests],
                         [(2, 15, 50), (6, 15, 50)])
        self.assertTrue(all(not r.use_total for r in requests))
        self.assertEqual(combine_public_decisions(
            (r, summarize_local(r)) for r in requests), ((5, 6), ()))
        self.assert_sound_public_board(4, opened, 2)

    def test_full_hidden_six_cells_can_use_global_total(self):
        shown = (0, 1, 2, 3, 4, 5, 6, 7, 8, 10)
        mines = {9, 11}
        opened = tuple((i, len(mines & neighbors(4, i))) for i in shown)
        requests = from_public_board(4, opened, 2)
        self.assertTrue(requests)
        self.assertTrue(all(r.use_total and r.total == 2 for r in requests))
        self.assert_sound_public_board(4, opened, 2)

    def test_finite_four_by_four_public_boards(self):
        rng = Random(20261026)
        for _ in range(120):
            shown = tuple(sorted(rng.sample(range(16), rng.randrange(3, 8))))
            hidden = tuple(i for i in range(16) if i not in shown)
            total = rng.randrange(4)
            mines = set(rng.sample(hidden, total))
            opened = tuple((i, len(mines & neighbors(4, i)))
                           for i in shown)
            self.assert_sound_public_board(4, opened, total)

    def test_public_board_contract_and_merge_errors(self):
        malformed = [
            ([(0, 0)] * 3, None),
            ([(0, 0), (1, 0)], None),
            ([(0, 0), (1, 0), (2, 0)] * 9, None),
            ([(0, 0), (1, 0), (2, True)], None),
            ([(0, 0), (1, 0), (2, 0)], True),
            ([(0, 0), (1, 0), (2, 0)], 14),
        ]
        for clues, total in malformed:
            with self.subTest(clues=clues, total=total):
                with self.assertRaises(ValueError):
                    from_public_board(4, clues, total)
        request = from_public_clues(3, ((0, 1), (2, 1), (7, 1)), 2)
        self.assertIsNone(combine_public_decisions([(request, None)]))
        for invalid in [(64, 0, 1), (1, 1, 1),
                        (1, 0, 0), (True, 0, 1)]:
            with self.assertRaises(ValueError):
                combine_public_decisions([(request, invalid)])
        self.assertEqual(combine_public_decisions([]), ((), ()))


if __name__ == "__main__":
    unittest.main()
