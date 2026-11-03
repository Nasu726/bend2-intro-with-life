"""Regression tests for the independent Bend no-guess certificate checker."""
from itertools import combinations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from independent_certificate import verify_certificate


class CertificateTests(unittest.TestCase):
    def test_known_bend_witness(self):
        self.assertEqual(len(verify_certificate(40960, (0, 12, 14))), 14)

    def test_crosscheck_all_protected_two_mine_layouts(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
        from noguess_reference import verify_no_guess
        accepted = 0
        for mines in combinations(range(16), 2):
            mask = sum(1 << i for i in mines)
            if mask & 0b110011:
                continue
            trace = verify_no_guess(4, 4, frozenset(mines), 0)
            if trace is None:
                continue
            self.assertEqual(len(verify_certificate(mask, trace)), 14)
            accepted += 1
        self.assertEqual(accepted, 66)

    def test_rejects_safe_but_unjustified_click(self):
        # Mines at 2 and 8; cell 6 is safe but is not forced after click 0.
        with self.assertRaisesRegex(ValueError, "guess"):
            verify_certificate((1 << 2) | (1 << 8), (0, 6))

    def test_rejects_incomplete_and_forged_witnesses(self):
        for mask, trace in ((40960, (0,)), (40960, (0, 14)),
                            (40960, (0, 12, 12, 14)),
                            (40960, (0, 13)), (40960, (0, 16)),
                            (1 << 20, (0,)), (0, (0,)),
                            ((1 << 0) | (1 << 15), (0,))):
            with self.subTest(mask=mask, trace=trace):
                with self.assertRaises(ValueError):
                    verify_certificate(mask, trace)


if __name__ == "__main__":
    unittest.main()
