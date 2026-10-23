"""Finite checks for Python-only 10x10 candidate generation/certificates.

This is not a Bend typecheck, GUI acceptance test or universal theorem.
"""
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import noguess_reference as ref
import nxn_noguess_generator as generator
import nxn_board_oracle as board
from itertools import combinations


class NoGuessGenerationContracts(unittest.TestCase):
    def test_standard_ten_by_ten_ten_mines_is_reproducible_and_nontrivial(self):
        cert = generator.generate_no_guess_frontier(10, 10, 10, 0, 20261023)
        self.assertEqual(cert.mines, frozenset({4, 29, 34, 36, 37, 49, 50, 56, 72, 77}))
        self.assertEqual(cert.clicks, (0, 14, 5, 6, 24, 35, 38, 39, 46, 47, 48, 57, 67))
        self.assertGreater(len(cert.clicks), 1)
        self.assertTrue(generator.verify_certificate(cert))
        self.assertEqual(cert, generator.generate_no_guess_frontier(10, 10, 10, 0, 20261023))
        self.assertFalse(cert.mines & {0, *ref.neighbors(0, 10, 10)})
        view = ref.Visible(10, 10, 10, ())
        state = board.new_game(10, cert.mines)
        for move in cert.clicks:
            self.assertNotIn(move, cert.mines)
            view = ref.expose(cert.mines, view, move)
            state = board.click(state, move)
            self.assertEqual(dict(view.opened), dict(state.opened))
            self.assertEqual(state.mines, cert.mines)
        self.assertEqual(len(view.opened), 90)
        self.assertEqual(state.phase, "Won")

    def test_arbitrary_first_click_and_small_board(self):
        cert = generator.generate_no_guess_frontier(4, 4, 2, 15, 2026)
        self.assertEqual(cert.first_click, 15)
        self.assertTrue(generator.verify_certificate(cert))
        self.assertFalse(cert.mines & {15, *ref.neighbors(15, 4, 4)})

    def test_small_certificate_against_independent_full_layout_enumeration(self):
        cert = generator.generate_no_guess_frontier(4, 4, 2, 15, 2026)
        view = ref.Visible(4, 4, 2, ())
        for position, move in enumerate(cert.clicks):
            if position:
                hidden = set(range(16)) - dict(view.opened).keys()
                layouts = [frozenset(pair) for pair in combinations(sorted(hidden), 2)
                           if all(sum(q in pair for q in ref.neighbors(p, 4, 4)) == clue
                                  for p, clue in view.opened)]
                self.assertTrue(layouts)
                self.assertTrue(all(move not in layout for layout in layouts))
            view = ref.expose(cert.mines, view, move)
        self.assertEqual(len(view.opened), 14)

    def test_rejects_guess_and_incomplete_or_extended_traces(self):
        cert = generator.generate_no_guess_frontier(10, 10, 10, 0, 20261023)
        for changed in (
            replace(cert, clicks=(0, 4)),
            replace(cert, clicks=cert.clicks[:-1]),
            replace(cert, clicks=cert.clicks + (cert.clicks[-1],)),
            replace(cert, clicks=(0, 99)),
            replace(cert, clicks=(1,) + cert.clicks[1:]),
            replace(cert, mine_count=9),
            replace(cert, mines=frozenset({0, *list(cert.mines)[1:]})),
            replace(cert, clicks=(0, True)),
            replace(cert, clicks=(0, 100)),
        ):
            with self.subTest(changed=changed):
                self.assertFalse(generator.verify_certificate(changed))
        self.assertFalse(generator.verify_certificate(None))

    def test_exhaustion_and_budget_are_not_certificates(self):
        with self.assertRaises(ref.GenerationFailed):
            generator.generate_no_guess_frontier(10, 10, 10, 0, 20261023,
                                                 attempts=2, node_limit=1)
        cert = generator.generate_no_guess_frontier(10, 10, 10, 0, 20261023)
        self.assertFalse(generator.verify_certificate(cert, node_limit=1))
        with patch.object(generator, "verify_no_guess_frontier", return_value=None):
            with self.assertRaises(ref.GenerationFailed):
                generator.generate_no_guess_frontier(10, 10, 10, 0, 20261023,
                                                     attempts=2)

    def test_invalid_dimensions_and_type_coercions(self):
        bad = ((0, 10, 1, 0), (10, 0, 1, 0), (101, 100, 1, 0),
               (10, 10, 100, 0), (10, 10, 10, 100),
               (True, 10, 1, 0), (10, 10, True, 0),
               (10, 10, 10, False), (10, 10, 10.0, 0))
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                generator.generate_no_guess_frontier(*args, seed=1)
        for kwargs in ({"seed": True}, {"seed": 1, "attempts": False},
                       {"seed": 1, "node_limit": True},
                       {"seed": 1, "attempts": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                generator.generate_no_guess_frontier(10, 10, 10, 0, **kwargs)
        with self.assertRaises(ValueError):
            generator.generate_no_guess_frontier(2, 2, 1, 0, 1)


if __name__ == "__main__":
    unittest.main()
