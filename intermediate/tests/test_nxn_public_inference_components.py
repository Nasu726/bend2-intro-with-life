"""Disconnected-frontier regression checks against full-board enumeration."""
from itertools import combinations
import random
import unittest

from nxn_public_inference import infer


def neighbors(n, i):
    x, y = i % n, i // n
    return {j for j in range(n*n) if j != i and
            abs(j % n - x) <= 1 and abs(j // n - y) <= 1}


def brute(n, mine_count, opened, flags=()):
    """Independent whole-board oracle, deliberately not using components."""
    hidden = set(range(n*n)) - {i for i, _ in opened}
    models = []
    for combo in combinations(sorted(hidden), mine_count):
        mines = set(combo)
        if all(len(neighbors(n, i) & mines) == clue
               for i, clue in opened):
            models.append(mines)
    if not models:
        return "contradiction", (), ()
    return ("ok", tuple(sorted(hidden - set.union(*models) - set(flags))),
            tuple(sorted(set.intersection(*models))))


class DisconnectedFrontier(unittest.TestCase):
    def compare(self, n, mines, opened, flags=(), limit=3):
        observations = tuple((i, len(neighbors(n, i) & mines))
                             for i in opened)
        actual = infer(n, len(mines), observations, flags,
                       max_frontier=limit)
        self.assertEqual((actual.status, actual.safe, actual.forced_mines),
                         brute(n, len(mines), observations, flags),
                         (n, mines, observations, flags))

    def test_disconnected_frontier_exceeds_total_limit(self):
        result = infer(10, 10, ((0, 0), (99, 0)), max_frontier=3)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.safe, (1, 10, 11, 88, 89, 98))
        self.assertEqual(result.forced_mines, ())
        self.assertEqual(infer(10, 10, ((11, 0),),
                               max_frontier=3).status, "limit")

    def test_global_mine_budget_filters_local_models(self):
        clues = ((0, 1), (24, 1))
        self.assertEqual(infer(5, 1, clues, max_frontier=3).status,
                         "contradiction")
        result = infer(5, 2, clues, max_frontier=3)
        self.assertEqual((result.status, len(result.safe),
                          result.forced_mines), ("ok", 17, ()))
        self.assertEqual((result.status, result.safe, result.forced_mines),
                         brute(5, 2, clues))
        result = infer(5, 1, ((0, 0), (24, 1)), max_frontier=3)
        self.assertEqual((result.status, result.safe, result.forced_mines),
                         brute(5, 1, ((0, 0), (24, 1))))

    def test_flags_are_not_assumed_mines(self):
        clues = ((0, 0), (24, 1))
        flags = (1, 23)
        result = infer(5, 1, clues, flags, max_frontier=3)
        self.assertEqual((result.status, result.safe, result.forced_mines),
                         brute(5, 1, clues, flags))
        self.assertNotIn(1, result.safe)
        self.assertNotIn(23, result.safe)

    def test_disconnected_random_finite_oracle(self):
        rng = random.Random(20261024)
        # Corner clues on a 5x5 board have two disjoint 3-cell frontiers.
        for mine_count in range(4):
            for _ in range(30):
                mines = set(rng.sample(range(25), mine_count))
                opened = tuple(i for i in (0, 24) if i not in mines)
                if len(opened) != 2:
                    continue
                flags = tuple(i for i in (1, 23) if i not in opened
                              and rng.randrange(2))
                self.compare(5, mines, opened, flags)

    def test_no_public_clues_and_zero_frontier_limit(self):
        self.assertEqual(infer(3, 0, (), max_frontier=0).safe,
                         tuple(range(9)))
        self.assertEqual(infer(3, 9, (), max_frontier=0).forced_mines,
                         tuple(range(9)))
        self.assertEqual(infer(3, 1, ((0, 0),), max_frontier=0).status,
                         "limit")


if __name__ == "__main__":
    unittest.main()
