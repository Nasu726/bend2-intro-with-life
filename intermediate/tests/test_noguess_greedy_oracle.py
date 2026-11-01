"""Independent greedy replay for all 4x4 two-mine layouts and corner starts.

The oracle enumerates public candidate layouts and performs its own FIFO
zero expansion. This finite regression is not a general Bend proof.
"""
from itertools import combinations
import unittest

from intermediate.solutions import noguess_reference as reference
from intermediate.scripts.independent_certificate import adjacent, verify_certificate

CELLS = frozenset(range(16))
CORNERS = (0, 3, 12, 15)


def greedy_replay(mines, first):
    if first in mines:
        return None
    opened = {}

    def expose(click):
        pending = [click]
        while pending:
            cell = pending.pop(0)
            if cell in opened:
                continue
            if cell in mines:
                raise AssertionError("oracle opened a mine")
            clue = len(adjacent(cell) & mines)
            opened[cell] = clue
            if clue == 0:
                pending.extend(sorted(adjacent(cell) - opened.keys()))

    expose(first)
    trace = [first]
    while len(opened) < 14:
        hidden = sorted(CELLS - opened.keys())
        models = []
        for pair in combinations(hidden, 2):
            candidate = frozenset(pair)
            if all(len(adjacent(cell) & candidate) == clue
                   for cell, clue in opened.items()):
                models.append(candidate)
        if not models or mines not in models:
            raise AssertionError("public enumeration lost the true board")
        possibly_mined = frozenset().union(*models)
        forced = [cell for cell in hidden if cell not in possibly_mined]
        if not forced:
            return None
        move = forced[0]
        expose(move)
        trace.append(move)
    return tuple(trace)


class IndependentGreedyOracleTests(unittest.TestCase):
    def test_all_layouts_at_four_corners(self):
        accepted = rejected = protected = 0
        for pair in combinations(range(16), 2):
            mines = frozenset(pair)
            mask = sum(1 << cell for cell in mines)
            for first in CORNERS:
                expected = greedy_replay(mines, first)
                actual = reference.verify_no_guess(4, 4, mines, first)
                with self.subTest(mines=pair, first=first):
                    self.assertEqual(actual, expected)
                    if expected is None:
                        rejected += 1
                        continue
                    accepted += 1
                    if not mines & ({first} | adjacent(first)):
                        self.assertEqual(
                            len(verify_certificate(mask, actual,
                                                   first_click=first)), 14)
                        protected += 1
        self.assertEqual((accepted, rejected, protected), (276, 204, 264))

    def test_known_bend_witness(self):
        self.assertEqual(greedy_replay(frozenset((13, 15)), 0), (0, 12, 14))


if __name__ == "__main__":
    unittest.main()
