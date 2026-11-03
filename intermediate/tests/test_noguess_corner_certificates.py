"""Finite 4x4 no-guess regression across all corner symmetries."""
from itertools import combinations
import unittest

from intermediate.solutions import noguess_reference as reference
from intermediate.scripts.independent_certificate import adjacent, verify_certificate


def transform(index, rotations, reflect):
    x, y = index % 4, index // 4
    for _ in range(rotations):
        x, y = 3 - y, x
    if reflect:
        x = 3 - x
    return y * 4 + x


class CornerCertificateTests(unittest.TestCase):
    def test_all_layouts_and_protected_corner_certificates(self):
        accepted = rejected = certified = 0
        for pair in combinations(range(16), 2):
            base = frozenset(pair)
            baseline = reference.verify_no_guess(4, 4, base, 0)
            for rotations in range(4):
                for reflect in (False, True):
                    first = transform(0, rotations, reflect)
                    mines = frozenset(transform(i, rotations, reflect) for i in base)
                    trace = reference.verify_no_guess(4, 4, mines, first)
                    with self.subTest(pair=pair, rotations=rotations, reflect=reflect):
                        self.assertEqual(trace is None, baseline is None)
                        if trace is None:
                            rejected += 1
                            continue
                        accepted += 1
                        if not mines & ({first} | adjacent(first)):
                            mask = sum(1 << i for i in mines)
                            opened = verify_certificate(mask, trace, first_click=first)
                            self.assertEqual(len(opened), 14)
                            certified += 1
        self.assertEqual(accepted + rejected, 960)
        self.assertEqual(certified, 528)
        self.assertGreater(accepted, 0)
        self.assertGreater(rejected, 0)


if __name__ == "__main__":
    unittest.main()
