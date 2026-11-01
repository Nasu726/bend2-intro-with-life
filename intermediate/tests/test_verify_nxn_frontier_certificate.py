"""Independent frontier-mask certificate checks (no game/inference imports)."""
from itertools import combinations
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_nxn_frontier_certificate import Audit, _neighbors, _publicly_safe, audit


def brute_decision(n, mine_count, opened, target):
    """Whole-board combinations, intentionally unrelated to frontier masks."""
    hidden = sorted(set(range(n*n)) - opened.keys())
    models = [set(candidate) for candidate in combinations(hidden, mine_count)
              if all(sum(j in candidate for j in _neighbors(n, cell)) == clue
                     for cell, clue in opened.items())]
    if not models:
        return "contradiction"
    return "guess" if any(target in model for model in models) else "safe"


class FrontierCertificate(unittest.TestCase):
    def test_ten_by_ten_independent_certificate(self):
        mines = tuple(range(50, 60))
        self.assertEqual(audit(10, mines, 0, (0, 99), 90),
                         Audit("valid", 2, 90))
        self.assertEqual(audit(10, mines, 0, (0, 99), 90,
                               max_frontier=9),
                         Audit("limit", 1, 50, "frontier budget"))

    def test_ten_by_ten_only_public_clues_are_needed(self):
        # The first zero flood opens rows 0..4. The checker has no reference
        # to a true mine placement when deciding whether cell 99 is safe.
        opened = {}
        truth = set(range(50, 60))
        from verify_nxn_frontier_certificate import _reveal
        _reveal(10, truth, opened, 0)
        self.assertEqual(len(opened), 50)
        self.assertEqual(_publicly_safe(10, 10, opened, 99, 18), "safe")
        self.assertEqual(_publicly_safe(10, 10, opened, 50, 18), "guess")
        self.assertEqual(_publicly_safe(10, 10, opened, 99, 9), "limit")

    def test_reject_guess_mine_partial_and_forged_count(self):
        self.assertEqual(audit(3, (1, 8), 0, (0, 3), 7).status, "invalid")
        self.assertEqual(audit(10, tuple(range(50, 60)), 0,
                               (0, 50), 90).status, "invalid")
        self.assertEqual(audit(10, tuple(range(50, 60)), 0,
                               (0,), 50).reason, "not a victory")
        self.assertEqual(audit(10, tuple(range(50, 60)), 0,
                               (0, 99), 89).reason, "opened count mismatch")
        self.assertEqual(audit(10, tuple(range(50, 60)), 0,
                               (0, 99, 98), 90).reason, "clicks after victory")
        self.assertEqual(audit(3, (0,), 0, (0,), 8).reason,
                         "first click is mined")

    def test_existing_four_by_four_witness(self):
        self.assertEqual(audit(4, (1, 4), 0, (0, 2, 3), 14),
                         Audit("valid", 3, 14))

    def test_exhaustive_three_by_three_public_decisions(self):
        # Exhaust all 3x3 boards with at most two mines, and each visible
        # single clue from a genuinely safe opened cell. Unlike the new
        # verifier, the oracle enumerates entire mine placements.
        for mine_count in range(3):
            for placement in combinations(range(9), mine_count):
                mines = set(placement)
                for opened_cell in set(range(9)) - mines:
                    clue = sum(j in mines for j in _neighbors(3, opened_cell))
                    opened = {opened_cell: clue}
                    for target in set(range(9)) - {opened_cell}:
                        with self.subTest(mines=placement, opened=opened_cell,
                                          target=target):
                            self.assertEqual(
                                _publicly_safe(3, mine_count, opened, target, 8),
                                brute_decision(3, mine_count, opened, target))

    def test_random_multiple_clues_and_global_budget(self):
        rng = random.Random(20261025)
        for _ in range(80):
            mines = set(rng.sample(range(9), rng.randrange(4)))
            opened_cells = rng.sample(sorted(set(range(9)) - mines),
                                      rng.randrange(1, 4))
            opened = {cell: sum(j in mines for j in _neighbors(3, cell))
                      for cell in opened_cells}
            for target in set(range(9)) - opened.keys():
                self.assertEqual(
                    _publicly_safe(3, len(mines), opened, target, 8),
                    brute_decision(3, len(mines), opened, target))

    def test_invalid_input_types_and_ranges(self):
        cases = [
            (True, (), 0, (0,), 4),
            (1, (), 0, (0,), 1),
            (3, (True,), 0, (0,), 8),
            (3, (1, 1), 0, (0,), 7),
            (3, (1,), True, (0,), 8),
            (3, (), 0, (), 9),
            (3, (), 0, (False,), 9),
            (3, (), 0, (0,), True),
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                audit(*args)
        for limit in (-1, 21, True, 1.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                audit(3, (), 0, (0,), 9, max_frontier=limit)


if __name__ == "__main__":
    unittest.main()
