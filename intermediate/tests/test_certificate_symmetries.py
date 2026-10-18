"""Geometric metamorphic tests for the 4x4, two-mine no-guess certificate.

A rotation or reflection preserves adjacency, public deductions and zero
flooding. These tests extend first-click coverage beyond cell zero without
claiming a proof for arbitrary board sizes or mine counts.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from independent_certificate import verify_certificate


def transform(index, rotations, reflect):
    x, y = index % 4, index // 4
    for _ in range(rotations):
        x, y = 3 - y, x
    if reflect:
        x = 3 - x
    return 4 * y + x


def mapped_certificate(mask, trace, rotations, reflect):
    mapped_mask = sum(1 << transform(i, rotations, reflect)
                      for i in range(16) if mask & (1 << i))
    mapped_trace = tuple(transform(i, rotations, reflect) for i in trace)
    return mapped_mask, mapped_trace


class CertificateSymmetryTests(unittest.TestCase):
    def test_all_eight_square_symmetries_are_bijections(self):
        for rotations in range(4):
            for reflect in (False, True):
                with self.subTest(rotations=rotations, reflect=reflect):
                    mapped = {transform(i, rotations, reflect) for i in range(16)}
                    self.assertEqual(mapped, set(range(16)))

    def test_known_bend_certificate_at_each_corner(self):
        for rotations in range(4):
            for reflect in (False, True):
                mask, trace = mapped_certificate(40960, (0, 12, 14), rotations, reflect)
                with self.subTest(rotations=rotations, reflect=reflect):
                    self.assertEqual(len(verify_certificate(mask, trace,
                                                           first_click=trace[0])), 14)
                    self.assertIn(trace[0], (0, 3, 12, 15))

    def test_first_click_mismatch_is_rejected_after_transform(self):
        for rotations in range(4):
            for reflect in (False, True):
                mask, trace = mapped_certificate(40960, (0, 12, 14), rotations, reflect)
                other_corner = next(i for i in (0, 3, 12, 15) if i != trace[0])
                with self.subTest(rotations=rotations, reflect=reflect):
                    with self.assertRaisesRegex(ValueError, "declared first click"):
                        verify_certificate(mask, trace, first_click=other_corner)

    def test_symmetry_does_not_turn_a_guess_into_a_certificate(self):
        # The second click is safe on the true board, but not logically forced.
        for rotations in range(4):
            for reflect in (False, True):
                mask, trace = mapped_certificate((1 << 2) | (1 << 8),
                                                 (0, 6), rotations, reflect)
                with self.subTest(rotations=rotations, reflect=reflect):
                    with self.assertRaisesRegex(ValueError, "guess"):
                        verify_certificate(mask, trace, first_click=trace[0])


if __name__ == "__main__":
    unittest.main()
