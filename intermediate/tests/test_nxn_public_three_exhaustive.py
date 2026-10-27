"""Independent exhaustive 3x3 soundness audit for three-clue propagation.

The oracle enumerates complete mine layouts, while the reference solver only
receives public clues. This does not test Bend equivalence or arbitrary N.
"""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_public_three_fixpoint import model

N = 3
FULL = (1 << (N * N)) - 1
NEIGHBORS = {
    i: tuple(j for j in range(N * N)
             if j != i and abs(i % N - j % N) <= 1
             and abs(i // N - j // N) <= 1)
    for i in range(N * N)
}


def signatures():
    """Group all truth layouts by exactly three safely revealed numbers."""
    candidates = defaultdict(set)
    pairs = 0
    for truth in range(1 << (N * N)):
        safe = [i for i in range(N * N) if not truth & (1 << i)]
        for opened in combinations(safe, 3):
            values = tuple(sum(bool(truth & (1 << j)) for j in NEIGHBORS[i])
                           for i in opened)
            candidates[(opened, values)].add(truth)
            pairs += 1
    return candidates, pairs


def bitmask(indices):
    return sum(1 << i for i in indices)


class ExhaustiveThreeClueAudit(unittest.TestCase):
    def test_all_consistent_three_clue_public_states(self):
        candidates, pairs = signatures()
        self.assertEqual(pairs, 5376)
        self.assertEqual(len(candidates), 2176)
        exact = incomplete = 0
        for (opened, values), possible in candidates.items():
            public = tuple(zip(opened, values))
            result = model(N, public)
            self.assertIsNotNone(result, (public, "valid clues rejected"))
            inferred_mines, inferred_safe = map(bitmask, result)
            forced_mines, possible_mines = FULL, 0
            for truth in possible:
                forced_mines &= truth
                possible_mines |= truth
            forced_safe = FULL ^ possible_mines
            self.assertEqual(inferred_mines & ~forced_mines, 0, public)
            self.assertEqual(inferred_safe & ~forced_safe, 0, public)
            if (inferred_mines, inferred_safe) == (forced_mines, forced_safe):
                exact += 1
            else:
                incomplete += 1
        # Baseline for this intentionally incomplete single-clue rule.
        self.assertEqual((exact, incomplete), (1500, 676))

    def test_incompleteness_and_non_satisfiability_witnesses(self):
        candidates, _ = signatures()
        # Two full layouts force 6/7/8 safe, but this rule cannot infer them.
        partial = ((1, 1), (2, 0), (4, 1))
        self.assertEqual(model(N, partial), ((), (1, 2, 4, 5)))
        self.assertEqual(len(candidates[((1, 2, 4), (1, 0, 1))]), 2)
        # Every clue is locally feasible, but there is no global layout.
        impossible = ((0, 1), (1, 1), (7, 4))
        self.assertNotIn(((0, 1, 7), (1, 1, 4)), candidates)
        self.assertIsNotNone(model(N, impossible))


if __name__ == "__main__":
    unittest.main()
