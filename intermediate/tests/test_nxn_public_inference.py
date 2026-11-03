"""Independent finite-oracle checks for bounded N x N public inference.

These tests do not execute Bend or certify no-guess board generation.
"""
from itertools import combinations
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
from nxn_public_inference import infer


def neighbors(n, i):
    x, y = i % n, i // n
    return {j for j in range(n*n) if j != i and
            abs(j % n - x) <= 1 and abs(j // n - y) <= 1}


def brute(n, mine_count, opened, flags):
    """Enumerate whole-board placements, independent of frontier logic."""
    clues = dict(opened)
    hidden = set(range(n*n)) - clues.keys()
    models = []
    for combo in combinations(sorted(hidden), mine_count):
        mines = set(combo)
        if all(len(neighbors(n, i) & mines) == clue
               for i, clue in opened):
            models.append(mines)
    if not models:
        return "contradiction", (), ()
    certain_mines = set.intersection(*models)
    possible_mines = set.union(*models)
    return ("ok", tuple(sorted(hidden - possible_mines - set(flags))),
            tuple(sorted(certain_mines)))


class PublicInference(unittest.TestCase):
    def check(self, n, mines, opened, flags=()):
        clues = tuple((i, len(neighbors(n, i) & mines)) for i in opened)
        actual = infer(n, len(mines), clues, flags)
        self.assertEqual((actual.status, actual.safe, actual.forced_mines),
                         brute(n, len(mines), clues, flags),
                         (n, mines, clues, flags))
        self.assertFalse(set(actual.safe) & set(mines))
        self.assertTrue(set(actual.forced_mines) <= set(mines))

    def test_exhaustive_two_by_two_public_states(self):
        for mask in range(16):
            mines = {i for i in range(4) if mask & (1 << i)}
            safe = sorted(set(range(4)) - mines)
            for revealed in range(1 << len(safe)):
                opened = tuple(i for k, i in enumerate(safe)
                               if revealed & (1 << k))
                hidden = sorted(set(range(4)) - set(opened))
                for flagged in range(1 << len(hidden)):
                    flags = tuple(i for k, i in enumerate(hidden)
                                  if flagged & (1 << k))
                    self.check(2, mines, opened, flags)

    def test_three_by_three_random_public_states(self):
        rng = random.Random(20261024)
        for mask in range(512):
            mines = {i for i in range(9) if mask & (1 << i)}
            safe = sorted(set(range(9)) - mines)
            for _ in range(2):
                opened = tuple(i for i in safe if rng.randrange(2))
                hidden = sorted(set(range(9)) - set(opened))
                flags = tuple(i for i in hidden if rng.randrange(5) == 0)
                self.check(3, mines, opened, flags)

    def test_large_board_and_global_mine_budget(self):
        result = infer(10, 10, ((0, 0),))
        self.assertEqual(result.status, "ok")
        self.assertTrue({1, 10, 11} <= set(result.safe))
        self.assertNotIn(50, result.safe)
        self.assertNotIn(1, infer(10, 10, ((0, 0),), (1,)).safe)
        self.assertEqual(len(infer(100, 0, ((0, 0),)).safe), 9999)
        self.assertEqual(infer(10, 99, ((0, 3),)).forced_mines,
                         tuple(range(1, 100)))
        self.assertEqual(infer(10, 10, ((0, 0),), max_frontier=2).status,
                         "limit")

    def test_contradictions_and_bad_inputs(self):
        self.assertEqual(infer(2, 0, ((0, 1),)).status, "contradiction")
        self.assertEqual(infer(2, 4, ((0, 0),)).status, "contradiction")
        self.assertEqual(infer(2, 1, ((0, 4),)).status, "contradiction")
        for kwargs in (
            dict(n=1, mine_count=0, opened=()),
            dict(n=True, mine_count=0, opened=()),
            dict(n=2, mine_count=True, opened=()),
            dict(n=2, mine_count=0, opened=((0, 0), (0, 0))),
            dict(n=2, mine_count=0, opened=((4, 0),)),
            dict(n=2, mine_count=0, opened=((0, True),)),
            dict(n=2, mine_count=0, opened=((0, 0),), flags=(0,)),
            dict(n=2, mine_count=0, opened=(), flags=(1, 1)),
            dict(n=2, mine_count=0, opened=(), max_frontier=25),
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                infer(**kwargs)


if __name__ == "__main__":
    unittest.main()
