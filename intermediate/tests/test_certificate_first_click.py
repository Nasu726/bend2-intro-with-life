"""Exercise independent no-guess certificates for every 4x4 first click.

The Python reference supplies traces, but the certificate checker independently
re-enumerates every layout consistent with the public clues at each step.
"""
from itertools import combinations
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "solutions"))
from independent_certificate import adjacent, verify_certificate
from noguess_reference import verify_no_guess


class ArbitraryFirstClickCertificateTests(unittest.TestCase):
    def test_rotated_known_witness(self):
        # Rotate 180 degrees: 0,12,14 -> 15,3,1; mines 13,15 -> 2,0.
        self.assertEqual(len(verify_certificate((1 << 0) | (1 << 2),
                                                (15, 3, 1), first_click=15)), 14)
        # The original fixed-first-click behavior remains the default.
        self.assertEqual(len(verify_certificate(40960, (0, 12, 14))), 14)

    def test_all_first_clicks_against_reference(self):
        accepted = {}
        for first in range(16):
            candidates = sorted(set(range(16)) - {first} - adjacent(first))
            successes = 0
            for pair in combinations(candidates, 2):
                trace = verify_no_guess(4, 4, frozenset(pair), first)
                if trace is None:
                    continue
                mask = sum(1 << i for i in pair)
                with self.subTest(first=first, mines=pair):
                    self.assertEqual(len(verify_certificate(
                        mask, trace, first_click=first)), 14)
                successes += 1
            accepted[first] = successes
        self.assertEqual(accepted[0], 66)
        self.assertTrue(all(count > 0 for count in accepted.values()), accepted)

    def test_invalid_or_mismatched_first_click(self):
        for first in (False, True, 0.0, "0", None, -1, 16):
            with self.subTest(first=first):
                with self.assertRaises(ValueError):
                    verify_certificate(40960, (0, 12, 14), first_click=first)
        for mask, trace, first in (
            (40960, (0, 12, 14), 15),
            ((1 << 0) | (1 << 2), (15, 3, 1), 0),
            ((1 << 0) | (1 << 2), (15, 3, 1), 14),
        ):
            with self.subTest(mask=mask, first=first):
                with self.assertRaises(ValueError):
                    verify_certificate(mask, trace, first_click=first)


if __name__ == "__main__":
    unittest.main()
