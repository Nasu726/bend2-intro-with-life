"""Finite integration contract: N x N game truth never enters inference.

These are Python reference tests, not Bend N x N generator verification.
"""
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
import nxn_board_oracle as Game
import nxn_noguess_replay as Replay


class NoGuessReplay(unittest.TestCase):
    def test_ten_by_ten_two_region_board(self):
        mines = frozenset(range(50, 60))
        result = Replay.solve(10, mines, 0)
        self.assertEqual(result.status, 'won')
        self.assertEqual(result.clicks, (0, 99))
        self.assertEqual(result.opened_count, 90)
        self.assertTrue(Replay.verify(10, mines, result.clicks))
        self.assertFalse(Replay.verify(10, mines, (0,)))
        self.assertFalse(Replay.verify(10, mines, (0, 99, 60)))

    def test_ten_by_ten_frontier_exhaustive_oracle(self):
        # Independent finite oracle: enumerate all 2^10 possibilities for
        # row 5, constrained by the publicly visible numbers in row 4.
        mines = frozenset(range(50, 60))
        game = Game.click(Game.new_game(10, mines), 0)
        view = Game.public_view(game)
        self.assertEqual(len(view.opened), 50)
        self.assertEqual({i for i, _ in view.opened}, set(range(50)))
        models = []
        for mask in range(1 << 10):
            candidate = {50 + j for j in range(10) if mask & (1 << j)}
            if all(sum(other in candidate for other in range(50, 60)
                       if abs(other % 10 - i % 10) <= 1) == clue
                   for i, clue in view.opened if 40 <= i <= 49):
                models.append(candidate)
        self.assertEqual(models, [set(range(50, 60))])
        deduction = Replay.infer(view.n, view.mine_count, view.opened)
        self.assertEqual(deduction.status, 'ok')
        self.assertEqual(deduction.forced_mines, tuple(range(50, 60)))
        self.assertEqual(deduction.safe, tuple(range(60, 100)))

    def test_selection_strategy_changes_bounded_outcome(self):
        mines = frozenset(range(50, 60))
        # Choosing the first known-safe cell repeatedly enlarges the
        # connected frontier past 18. This is a limit, not a contradiction.
        lowest = Replay.solve(10, mines, 0, selection='lowest')
        self.assertEqual(lowest.status, 'limit')
        self.assertEqual(lowest.clicks[:2], (0, 60))
        self.assertFalse(Replay.verify(10, mines, lowest.clicks))
        highest = Replay.solve(10, mines, 0, selection='highest')
        self.assertEqual((highest.status, highest.clicks), ('won', (0, 99)))

    def test_small_boards_exhaustive_first_clicks(self):
        # 2x2: 15 non-full mine sets x four first clicks.
        for mask in range(15):
            mines = frozenset(i for i in range(4) if mask & (1 << i))
            for first in range(4):
                with self.subTest(mask=mask, first=first):
                    result = Replay.solve(2, mines, first)
                    self.assertIn(result.status, ('won', 'stuck'))
                    self.assertEqual(Replay.verify(2, mines, result.clicks),
                                     result.status == 'won')
                    self.assertEqual(result.clicks[0], first)

    def test_all_three_by_three_layouts_and_first_clicks(self):
        # All 511 non-full mine masks, all 9 first-click positions: 4599.
        # Every accepted certificate is replayed, including relocation when
        # the first click originally contained a mine.
        counts = {'won': 0, 'stuck': 0}
        for mask in range((1 << 9) - 1):
            mines = frozenset(i for i in range(9) if mask & (1 << i))
            for first in range(9):
                result = Replay.solve(3, mines, first)
                self.assertIn(result.status, counts)
                counts[result.status] += 1
                self.assertEqual(Replay.verify(3, mines, result.clicks),
                                 result.status == 'won')
        self.assertEqual(counts, {'won': 444, 'stuck': 4155})

    def test_no_guess_is_not_guaranteed_for_every_board(self):
        # The first click exposes only a numbered corner, with no forced safe
        # continuation; the solver must stop rather than guess.
        mines = frozenset((1, 8))
        result = Replay.solve(3, mines, 0)
        self.assertEqual(result.status, 'stuck')
        self.assertEqual(result.clicks, (0,))
        self.assertFalse(Replay.verify(3, mines, (0,)))
        self.assertFalse(Replay.verify(3, mines, (0, 3)))  # An unproved guess.

    def test_budget_and_limit_are_not_certificates(self):
        mines = frozenset(range(50, 60))
        budget = Replay.solve(10, mines, 0, max_moves=1)
        self.assertEqual((budget.status, budget.clicks), ('budget', (0,)))
        limit = Replay.solve(10, mines, 0, max_frontier=9)
        self.assertEqual((limit.status, limit.clicks), ('limit', (0,)))
        self.assertFalse(Replay.verify(10, mines, (0, 60), max_frontier=9))

    def test_inference_receives_only_public_view(self):
        mines = frozenset(range(50, 60))
        observed = []
        original = Replay.infer

        def spy(n, mine_count, opened, flags=(), max_frontier=18):
            observed.append((n, mine_count, opened, flags))
            self.assertIsInstance(opened, tuple)
            self.assertTrue(all(len(entry) == 2 for entry in opened))
            self.assertFalse(isinstance(opened, Game.State))
            return original(n, mine_count, opened, flags=flags,
                            max_frontier=max_frontier)
        with patch.object(Replay, 'infer', side_effect=spy):
            result = Replay.solve(10, mines, 0)
        self.assertEqual(result.status, 'won')
        self.assertTrue(observed)
        self.assertEqual(observed[0][0:2], (10, 10))
        self.assertEqual(observed[0][3], ())

    def test_standalone_example_output(self):
        process = subprocess.run(
            [sys.executable, str(Path(Replay.__file__))],
            capture_output=True, text=True, check=True)
        self.assertIn("highest: Replay(status='won', clicks=(0, 99), opened_count=90)",
                      process.stdout)
        self.assertIn('certificate: True', process.stdout)
        self.assertIn("lowest: Replay(status='limit'", process.stdout)

    def test_invalid_certificate_and_input_contract(self):
        mines = frozenset((1, 8))
        for clicks in ((), [], (True,), (0, 0.0), (0, 9), (0, -1)):
            with self.subTest(clicks=clicks), self.assertRaises(ValueError):
                Replay.verify(3, mines, clicks)
        for kwargs in (dict(max_moves=0), dict(max_moves=True),
                       dict(max_moves=1.5), dict(selection="random"),
                       dict(max_frontier=25), dict(max_frontier=True)):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Replay.solve(3, mines, 0, **kwargs)
        with self.assertRaises(ValueError):
            Replay.solve(3, mines, True)
        with self.assertRaises(ValueError):
            Replay.solve(3, mines, 9)


if __name__ == '__main__':
    unittest.main()
