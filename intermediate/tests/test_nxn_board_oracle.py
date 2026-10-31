"""Finite N x N reference contracts; these are Python tests, not Bend proofs."""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_board_oracle as board


class NxNBoardContracts(unittest.TestCase):
    def test_storage_and_row_major_coordinates(self):
        self.assertEqual(board.storage_depth(10), 7)  # 128 slots, 100 live.
        self.assertEqual(board.storage_depth(4), 4)
        self.assertEqual(board.storage_depth(8), 6)
        self.assertEqual(board.index(10, 0, 0), 0)
        self.assertEqual(board.index(10, 9, 0), 9)
        self.assertEqual(board.index(10, 0, 9), 90)
        self.assertEqual(board.index(10, 9, 9), 99)
        self.assertEqual(board.index(10, 5, 5), 55)
        for n in (2, 3, 4, 10, 17):
            self.assertEqual({board.index(n, x, y)
                              for y in range(n) for x in range(n)},
                             set(range(n * n)))

    def test_finite_non_wrapping_neighbors(self):
        for n in (2, 3, 4, 10, 17):
            self.assertEqual(set(board.neighbors(n, 0)), {1, n, n + 1})
            self.assertEqual(len(board.neighbors(n, n + 1)),
                             3 if n == 2 else 8)
            if n >= 3:
                self.assertNotIn(n * n - 1, board.neighbors(n, 0))
            for i in range(n * n):
                self.assertNotIn(i, board.neighbors(n, i))
                for j in board.neighbors(n, i):
                    self.assertIn(i, board.neighbors(n, j))
        self.assertEqual(set(board.neighbors(10, 9)), {8, 18, 19})

    def test_invalid_setup_and_coordinate_contract(self):
        for bad in (0, 1, -1, False, True, 10.0, "10"):
            with self.subTest(n=bad), self.assertRaises(ValueError):
                board.new_game(bad, frozenset())
        for bad in (False, True, -1, 100, 1.0, "1"):
            with self.subTest(i=bad), self.assertRaises(ValueError):
                board.new_game(10, frozenset({bad}))
        with self.assertRaises(ValueError):
            board.new_game(10, frozenset(range(100)))
        for x, y in ((10, 0), (0, 10), (-1, 0), (0, -1),
                     (True, 0), (0, False), (1.0, 0)):
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                board.index(10, x, y)

    def test_first_click_safe_relocation_and_public_separation(self):
        state = board.new_game(10, frozenset({0, 99}))
        self.assertIs(board.mark(state, 1), state)  # Fresh flags ignored.
        after = board.click(state, 0)
        self.assertEqual(after.mines, frozenset({1, 99}))
        self.assertEqual(len(after.mines), len(state.mines))
        self.assertIn(0, dict(after.opened))
        self.assertEqual(after.phase, "Playing")
        self.assertFalse(hasattr(board.public_view(after), "mines"))
        self.assertEqual(board.public_view(after).mine_count, 2)

    def test_invalid_clicks_flags_and_terminal_loss(self):
        state = board.new_game(10, frozenset({11, 99}))
        for invalid in (-1, 100, 127, False, True, 0.0, "0"):
            self.assertIs(board.click(state, invalid), state)
            self.assertIs(board.mark(state, invalid), state)
        state = board.click(state, 0)
        self.assertEqual(dict(state.opened)[0], 1)
        state = board.mark(state, 99)
        self.assertIn(99, state.flags)
        self.assertEqual(board.click(state, 99), state)
        state = board.mark(state, 99)
        self.assertNotIn(99, state.flags)
        lost = board.click(state, 11)
        self.assertEqual(lost.phase, "Lost")
        self.assertIs(board.click(lost, 2), lost)
        self.assertIs(board.mark(lost, 2), lost)

    def test_flagged_safe_cell_is_not_flood_opened(self):
        state = board.click(board.new_game(10, frozenset({11})), 0)
        self.assertEqual(state.phase, "Playing")
        state = board.mark(state, 99)
        self.assertIn(99, state.flags)
        flooded = board.click(state, 88)
        self.assertNotIn(99, dict(flooded.opened))
        self.assertIn(99, flooded.flags)
        self.assertEqual(flooded.phase, "Playing")
        unflagged = board.mark(flooded, 99)
        won = board.click(unflagged, 99)
        self.assertIn(99, dict(won.opened))
        for i in range(100):
            if i != 11:
                won = board.click(won, i)
        self.assertEqual(won.phase, "Won")
        self.assertNotIn(11, dict(won.opened))

    def test_zero_flood_and_winning_condition(self):
        empty = board.click(board.new_game(10, frozenset()), 0)
        self.assertEqual(empty.phase, "Won")
        self.assertEqual(len(empty.opened), 100)
        self.assertIs(board.click(empty, 99), empty)
        for n in (2, 3, 4, 10):
            state = board.new_game(n, frozenset({n * n - 1}))
            for i in range(n * n - 1):
                state = board.click(state, i)
                self.assertNotIn(n * n - 1, dict(state.opened))
                self.assertEqual(state.phase == "Won",
                                 len(state.opened) == n * n - 1)
            self.assertEqual(state.phase, "Won")

    def test_randomized_flood_matches_independent_grid_bfs(self):
        rng = random.Random(20261019)
        for n in (3, 4, 10):
            for _ in range(45):
                mines = frozenset(rng.sample(range(n * n), rng.randrange(n * n)))
                if len(mines) == n * n:
                    continue
                first = rng.choice(sorted(set(range(n * n)) - mines))
                state = board.click(board.new_game(n, mines), first)
                # Independent coordinate-based BFS, not board.neighbors().
                expected = {}
                todo = [first]
                while todo:
                    i = todo.pop(0)
                    if i in expected:
                        continue
                    x, y = i % n, i // n
                    adjacent = [yy * n + xx
                                for yy in range(n) for xx in range(n)
                                if max(abs(xx - x), abs(yy - y)) == 1]
                    count = len(set(adjacent) & mines)
                    expected[i] = count
                    if count == 0:
                        todo.extend(j for j in adjacent
                                    if j not in mines and j not in expected)
                self.assertEqual(dict(state.opened), expected)
                self.assertEqual(state.mines, mines)
                self.assertEqual(state.phase == "Won",
                                 len(expected) == n * n - len(mines))


if __name__ == "__main__":
    unittest.main()
