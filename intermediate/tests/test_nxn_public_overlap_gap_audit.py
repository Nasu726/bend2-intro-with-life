"""Python-only finite audit for two real, nonnested public clues.

Bend typecheck/execution of all 40 cases is in scripts/test_nxn_public_overlap_gap.py.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_public_overlap_gap import audit
from test_nxn_public_pair_gap import public_states


class PublicOverlapGap(unittest.TestCase):
    def test_560_states_and_40_overlap_improvements(self):
        self.assertEqual(len(public_states()), 560)
        self.assertEqual(len(audit()), 40)


if __name__ == "__main__":
    unittest.main()
