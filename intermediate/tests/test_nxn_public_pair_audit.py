"""Finite 3x3 public-state audit of the real two-clue subset witnesses.

This tests the Python oracle; the Bend subset implementation is checked
separately on all 48 public-derived cases in the dedicated CI script.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_public_pair_gap import audit, public_states
from test_nxn_public_many_fixpoint import model


class PublicPairGap(unittest.TestCase):
    def test_560_states_and_48_subset_improvements(self):
        self.assertEqual(len(public_states()), 560)
        self.assertEqual(len(audit()), 48)

    def test_safe_and_mine_witnesses(self):
        for clues in (((1, 1), (4, 1)), ((4, 4), (7, 1))):
            opened = tuple(i for i, _ in clues)
            self.assertEqual(model(3, clues, (), opened), ((), opened))
            self.assertEqual(len(public_states()[clues]), 4)


if __name__ == "__main__":
    unittest.main()
