"""Exhaustive 3x3 audit for the variable-clue *Python reference* model.

All 3^9 mine/hidden-safe/revealed-safe assignments are considered. Identical
public observations are grouped and compared against a separate all-layout
oracle. This is NOT an exhaustive Bend execution, a proof for arbitrary N,
or a completeness claim for single-clue propagation.
"""
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_public_many_fixpoint import model

N = 3
FULL = (1 << (N * N)) - 1
NEIGHBORS = {
    i: tuple(j for j in range(N*N) if i != j
             and abs(i % N - j % N) <= 1
             and abs(i // N - j // N) <= 1)
    for i in range(N*N)
}
EXPECTED_STATES = (1, 49, 560, 2176, 3088, 1922, 672, 144, 18, 1)
EXPECTED_COMPLETE = (1, 49, 472, 1500, 2360, 1754, 660, 144, 18, 1)
EXPECTED_INCOMPLETE = (0, 0, 88, 676, 728, 168, 12, 0, 0, 0)


def signatures():
    """Group every true layout/opened subset by its public-only digits."""
    possible = defaultdict(set)
    pairs = 0
    for truth in range(1 << (N*N)):
        safe = [i for i in range(N*N) if not truth & (1 << i)]
        for count in range(len(safe)+1):
            for opened in combinations(safe, count):
                values = tuple(sum(bool(truth & (1 << j)) for j in NEIGHBORS[i])
                               for i in opened)
                possible[(opened, values)].add(truth)
                pairs += 1
    return possible, pairs


def bits(items):
    return sum(1 << i for i in items)


class ExhaustiveManyClueAudit(unittest.TestCase):
    def test_all_consistent_3x3_public_states(self):
        candidates, pairs = signatures()
        self.assertEqual(pairs, 3**9)  # each cell is mine, hidden safe or revealed
        self.assertEqual(len(candidates), 8631)
        states, complete, incomplete = Counter(), Counter(), Counter()
        for (opened, values), layouts in candidates.items():
            public = tuple(zip(opened, values))
            result = model(N, public, (), opened, N*N+1)
            self.assertIsInstance(result, tuple, public)
            inferred_mines, inferred_safe = map(bits, result)
            forced_mines, possible_mines = FULL, 0
            for truth in layouts:
                forced_mines &= truth
                possible_mines |= truth
            forced_safe = FULL ^ possible_mines
            self.assertEqual(inferred_mines & ~forced_mines, 0, public)
            self.assertEqual(inferred_safe & ~forced_safe, 0, public)
            count = len(opened)
            states[count] += 1
            if (inferred_mines, inferred_safe) == (forced_mines, forced_safe):
                complete[count] += 1
            else:
                incomplete[count] += 1
        self.assertEqual(tuple(states[k] for k in range(10)), EXPECTED_STATES)
        self.assertEqual(tuple(complete[k] for k in range(10)), EXPECTED_COMPLETE)
        self.assertEqual(tuple(incomplete[k] for k in range(10)), EXPECTED_INCOMPLETE)
        self.assertEqual(sum(complete.values()), 6959)
        self.assertEqual(sum(incomplete.values()), 1672)

    def test_two_clue_subset_gap_witness(self):
        # Both digits have one mine among {0,2,3,5}; the second additionally
        # sees {6,7,8}, so these three cells are safe by subtracting sets.
        public = ((1, 1), (4, 1))
        self.assertEqual(model(N, public, (), (1, 4)), ((), (1, 4)))
        candidates, _ = signatures()
        layouts = candidates[((1, 4), (1, 1))]
        self.assertEqual(len(layouts), 4)
        self.assertTrue(all(not truth & (1 << i) for truth in layouts
                            for i in (6, 7, 8)))


if __name__ == "__main__":
    unittest.main()
