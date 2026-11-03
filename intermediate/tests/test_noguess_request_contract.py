"""The no-guess reference rejects malformed requests before inference.

Invalid input is different from a valid position with no forced safe move.
This Python auxiliary checker does not establish a Bend-wide theorem.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import noguess_reference as ref


class NoGuessRequestContractTests(unittest.TestCase):
    MINES = frozenset((13, 15))

    def test_invalid_verification_dimensions(self):
        for width, height in ((False, 4), (4, True), (4.0, 4),
                              (4, 4.0), ("4", 4), (4, "4"),
                              (0, 4), (4, -1)):
            with self.subTest(width=width, height=height):
                with self.assertRaises(ValueError):
                    ref.verify_no_guess(width, height, self.MINES, 0)

    def test_invalid_verification_mines(self):
        for mines in ({13, 15}, [13, 15], (13, 15),
                      frozenset((False, 15)), frozenset((13.0, 15)),
                      frozenset((-1, 15)), frozenset((13, 16))):
            with self.subTest(mines=mines):
                with self.assertRaises(ValueError):
                    ref.verify_no_guess(4, 4, mines, 0)

    def test_invalid_verification_click_and_budget(self):
        for click in (False, True, 0.0, "0", -1, 16):
            with self.subTest(click=click):
                with self.assertRaises(ValueError):
                    ref.verify_no_guess(4, 4, self.MINES, click)
        for limit in (False, True, 10.0, "10", None, -1):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    ref.verify_no_guess(4, 4, self.MINES, 0, limit=limit)

    def test_invalid_generation_request(self):
        valid = (4, 4, 2, 0)
        for index, replacements in (
            (0, (False, 4.0, "4", 0)),
            (1, (True, 4.0, "4", -1)),
            (2, (False, True, 2.0, "2", -1)),
            (3, (False, True, 0.0, "0", -1, 16)),
        ):
            for replacement in replacements:
                args = list(valid)
                args[index] = replacement
                with self.subTest(args=args):
                    with self.assertRaises(ValueError):
                        ref.generate(*args, seed=2026)
        for seed in (False, True, 2026.0, "2026", None):
            with self.subTest(seed=seed):
                with self.assertRaises(ValueError):
                    ref.generate(*valid, seed=seed)
        for attempts in (False, True, 1.0, "1", None, 0, -1):
            with self.subTest(attempts=attempts):
                with self.assertRaises(ValueError):
                    ref.generate(*valid, seed=2026, attempts=attempts)

    def test_valid_but_unprovable_is_not_an_invalid_request(self):
        self.assertIsNone(ref.verify_no_guess(4, 4, self.MINES, 0, limit=0))
        self.assertEqual(ref.verify_no_guess(4, 4, self.MINES, 0), (0, 12, 14))
        self.assertEqual(ref.generate(4, 4, 2, 0, seed=2026),
                         ref.generate(4, 4, 2, 0, seed=2026))


if __name__ == "__main__":
    unittest.main()
