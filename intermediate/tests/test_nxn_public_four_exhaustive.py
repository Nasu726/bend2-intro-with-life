"""Exhaustive 3x3 public-only audit of the four-clue Python reference.

Enumerate every truth layout with four safely revealed cells, then group
identical public states. The full-layout oracle is separate from the local
single-clue fixed-point rule. This is not an arbitrary-N proof or an exhaustive
Bend execution test.
"""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_public_four_fixpoint import model

N = 3
FULL = (1 << (N * N)) - 1
NEIGHBORS = {
    i: tuple(j for j in range(N * N)
             if j != i and abs(i % N - j % N) <= 1
             and abs(i // N - j // N) <= 1)
    for i in range(N * N)
}


def signatures():
    """Group all valid mine layouts by four safely revealed clue digits."""
    candidates = defaultdict(set)
    pairs = 0
    for truth in range(1 << (N * N)):
        safe = [i for i in range(N * N) if not truth & (1 << i)]
        for opened in combinations(safe, 4):
            values = tuple(sum(bool(truth & (1 << j)) for j in NEIGHBORS[i])
                           for i in opened)
            candidates[(opened, values)].add(truth)
            pairs += 1
    return candidates, pairs


def bitmask(indices):
    return sum(1 << i for i in indices)


class ExhaustiveFourClueAudit(unittest.TestCase):
    def test_all_consistent_four_clue_public_states(self):
        candidates, pairs = signatures()
        self.assertEqual(pairs, 4032)
        self.assertEqual(len(candidates), 3088)
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
        # Local propagation is sound here but not globally complete.
        self.assertEqual((exact, incomplete), (2360, 728))

    def test_concrete_gap_witness(self):
        # Clues jointly force mine 4 and safety 3/5/7, but no single clue
        # alone can start the deduction chain.
        public = ((0, 1), (1, 1), (2, 1), (6, 1))
        self.assertEqual(model(N, public), ((), (0, 1, 2, 6)))
        candidates, _ = signatures()
        possible = candidates[((0, 1, 2, 6), (1, 1, 1, 1))]
        self.assertTrue(possible)
        self.assertTrue(all(truth & (1 << 4) for truth in possible))
        self.assertTrue(all(not truth & (1 << i) for truth in possible
                            for i in (3, 5, 7)))


if __name__ == "__main__":
    unittest.main()
