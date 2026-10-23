"""Tests for the independent exhaustive certificate audit."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_nxn_certificate import Audit, _safe_choices, audit


class IndependentCertificateAudit(unittest.TestCase):
    def test_documented_four_by_four_witness(self):
        self.assertEqual(audit(4, (1, 4), 0, (0, 2, 3), 14),
                         Audit("valid", 3, 14))

    def test_zero_mines_and_near_full(self):
        self.assertEqual(audit(3, (), 0, (0,), 9), Audit("valid", 1, 9))
        self.assertEqual(audit(100, tuple(range(1, 10000)), 0, (0,), 1),
                         Audit("valid", 1, 1))

    def test_forged_or_incomplete_witness(self):
        examples = [
            ((1, 4), (0, 2), 14),  # incomplete
            ((1, 4), (0, 2, 3), 13),  # false opened count
            ((1, 4), (0, 3, 2), 14),  # not the min-safe policy
            ((1, 4), (0, 1, 2, 3), 14),  # mine clicked
            ((1, 4), (0, 2, 3, 3), 14),  # click after victory
            ((0, 4), (0,), 14),  # first-click mine
        ]
        for mines, clicks, opened in examples:
            with self.subTest(mines=mines, clicks=clicks):
                self.assertEqual(audit(4, mines, 0, clicks, opened).status,
                                 "invalid")

    def test_independent_public_safe_set(self):
        # One public clue 2 at 0, total two mines: every non-neighbor is safe.
        status, safe = _safe_choices(4, 2, {0: 2}, 1000)
        self.assertEqual(status, "ok")
        self.assertEqual(safe, (2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15))
        self.assertEqual(_safe_choices(4, 2, {0: 2}, 1)[0], "limit")

    def test_bounded_oracle_is_not_a_success(self):
        self.assertEqual(audit(4, (1, 4), 0, (0, 2, 3), 14,
                               max_hypotheses=1).status, "limit")

    def test_reject_invalid_input(self):
        for args in [(True, (), 0, (0,), 1), (1, (), 0, (0,), 1),
                     (3, (True,), 0, (0,), 8), (3, (1, 1), 0, (0,), 7),
                     (3, (2, 1), 0, (0,), 7), (3, (), True, (0,), 9),
                     (3, (), 0, (), 9), (3, (), 0, (False,), 9),
                     (3, (), 0, (0,), True)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                audit(*args)
        with self.assertRaises(ValueError):
            audit(3, (), 0, (0,), 9, max_hypotheses=0)


if __name__ == "__main__":
    unittest.main()
