"""Malformed no-guess witnesses must fail cleanly, never coerce indices."""
import unittest

from independent_certificate import verify_certificate


class CertificateInputContractTests(unittest.TestCase):
    MASK = 40960
    TRACE = (0, 12, 14)

    def test_list_and_tuple_witnesses_are_equivalent(self):
        expected = verify_certificate(self.MASK, self.TRACE)
        self.assertEqual(verify_certificate(self.MASK, list(self.TRACE)), expected)
        self.assertEqual(len(expected), 14)

    def test_malformed_mine_masks_are_rejected(self):
        for mask in (False, True, 40960.0, "40960", -1, 1 << 16, 0, 1):
            with self.subTest(mask=mask):
                with self.assertRaises(ValueError):
                    verify_certificate(mask, self.TRACE)

    def test_malformed_click_sequences_are_rejected(self):
        bad = (
            None, "0,12,14", b"0,12,14", {0: 0, 12: 12, 14: 14},
            iter(self.TRACE), (), (1, 12, 14),
            (False, 12, 14), (0, True, 14), (0, 12, False),
            (0, 12.0, 14), (0, "12", 14), (0, [], 14),
            (0, -1, 14), (0, 16, 14), (0, 12, 12),
        )
        for clicks in bad:
            with self.subTest(clicks=repr(clicks)):
                with self.assertRaises(ValueError):
                    verify_certificate(self.MASK, clicks)

    def test_valid_shape_is_not_enough_to_certify_a_win(self):
        for clicks in ((0,), (0, 12), (0, 14), (0, 12, 13)):
            with self.subTest(clicks=clicks):
                with self.assertRaises(ValueError):
                    verify_certificate(self.MASK, clicks)


if __name__ == "__main__":
    unittest.main()
