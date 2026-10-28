"""Two-clue exact-overlap audit; 560 Python states, not 560 Bend runs."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_public_pair_overlap_audit import audit


class PublicOverlapAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.counts = audit()

    def test_all_public_states(self):
        self.assertEqual(self.counts["nested"] + self.counts["nonnested"], 560)
        self.assertEqual(self.counts["improved"], 88)

    def test_non_nested_bend_fixtures(self):
        self.assertEqual(len(self.cases), 40)
        self.assertEqual(self.counts["nonnested_gap"], 40)
        self.assertEqual(self.counts["nested_gap"], 48)

    def test_safe_and_mine_improvements_are_counted_separately(self):
        self.assertEqual(self.counts["improved_safe"], 64)
        self.assertEqual(self.counts["improved_mines"], 64)


if __name__ == "__main__":
    unittest.main()
