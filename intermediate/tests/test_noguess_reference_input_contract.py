"""Validate the reference game engine's trust boundary and generated certificates.

These checks concern Python's auxiliary checker, not a Bend-wide theorem.
"""
from itertools import combinations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import noguess_reference as ref


class ReferenceBoundaryTests(unittest.TestCase):
    def test_rejects_forged_visible_history(self):
        mines = frozenset((13, 15))
        cases = (
            ((16, 0),), ((-1, 0),), ((13, 0),),
            ((0, 1),),  # correct clue is zero
            ((0, 0), (0, 0)),  # repeated open cell
            ((0, 0), (0, 1)),  # contradictory repeat
        )
        for opened in cases:
            with self.subTest(opened=opened):
                view = ref.Visible(4, 4, 2, opened)
                with self.assertRaises(ValueError):
                    ref.expose(mines, view, 0)

    def test_preserves_valid_opened_history(self):
        mines = frozenset((13, 15))
        view = ref.expose(mines, ref.Visible(4, 4, 2, ()), 0)
        self.assertEqual(ref.expose(mines, view, 0), view)
        self.assertEqual(ref.verify_no_guess(4, 4, mines, 0), (0, 12, 14))

    def test_rejects_non_integer_public_observations(self):
        # bool is a subclass of int, and 0.0 == 0; neither is a valid cell/clue.
        bad_opened = (
            ((False, 0),), ((True, 0),), ((0, False),),
            ((0, True),), ((0.0, 0),), ((0, 0.0),),
            (("0", 0),), ((0, "0"),),
            ((0,),), ((0, 0, 0),), (False,),
        )
        for opened in bad_opened:
            with self.subTest(opened=opened):
                view = ref.Visible(4, 4, 2, opened)
                self.assertEqual(ref.consistent_models(view), [])
                with self.assertRaises(ValueError):
                    ref.provably_safe(view)
                with self.assertRaises(ValueError):
                    ref.expose(frozenset((13, 15)), view, 0)

    def test_rejects_malformed_public_dimensions_and_limits(self):
        for view in (
            ref.Visible(False, 4, 2, ()),
            ref.Visible(4, True, 2, ()),
            ref.Visible(4.0, 4, 2, ()),
            ref.Visible(4, 4, True, ()),
            ref.Visible(4, 4, 2.0, ()),
            ref.Visible(4, 4, -1, ()),
            ref.Visible(4, 4, 2, []),
        ):
            with self.subTest(view=view):
                self.assertEqual(ref.consistent_models(view), [])
                with self.assertRaises(ValueError):
                    ref.provably_safe(view)
                with self.assertRaises(ValueError):
                    ref.expose(frozenset((13, 15)), view, 0)
        valid = ref.Visible(4, 4, 2, ((0, 0),))
        for limit in (False, True, 120.0, "120", None):
            with self.subTest(limit=limit):
                self.assertEqual(ref.consistent_models(valid, limit=limit), [])
                with self.assertRaises(ValueError):
                    ref.provably_safe(valid, limit=limit)

    def test_rejects_coercible_truth_and_click_indices(self):
        valid = ref.Visible(4, 4, 2, ())
        for click in (False, True, 0.0, "0"):
            with self.subTest(click=click):
                with self.assertRaises(ValueError):
                    ref.expose(frozenset((13, 15)), valid, click)
        for mines in (frozenset((False, 15)), frozenset((13.0, 15)), {13, 15}):
            with self.subTest(mines=mines):
                with self.assertRaises(ValueError):
                    ref.expose(mines, valid, 0)

    def test_generator_witness_has_only_publicly_forced_clicks(self):
        # Independently re-enumerate public candidates: do not call the
        # implementation's provably_safe or neighbors from this test.
        for seed in range(6):
            mines, trace = ref.generate(4, 4, 2, 0, seed=seed)
            opened = ref.Visible(4, 4, 2, ())
            self.assertEqual(trace[0], 0)
            for n, clicked in enumerate(trace):
                self.assertNotIn(clicked, mines)
                if n:
                    placements = tuple(
                        frozenset(pair)
                        for pair in combinations(
                            set(range(16)) - dict(opened.opened).keys(), 2
                        )
                        if all(
                            sum(
                                abs(p // 4 - q // 4) <= 1
                                and abs(p % 4 - q % 4) <= 1
                                and q != p
                                for q in pair
                            ) == clue
                            for p, clue in opened.opened
                        )
                    )
                    self.assertTrue(placements)
                    self.assertTrue(all(clicked not in x for x in placements))
                opened = ref.expose(mines, opened, clicked)
            self.assertEqual(len(opened.opened), 14)


if __name__ == "__main__":
    unittest.main()
