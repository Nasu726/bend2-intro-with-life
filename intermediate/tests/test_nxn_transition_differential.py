"""Exhaustive 3x3 transition differential checks, not Bend proofs.

The second implementation computes adjacency from coordinate distances rather
than calling the reference model's neighbors/click/mark implementation.
"""
from collections import deque
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_board_oracle as board


def independent_step(state, operation, cell):
    """A separately written finite game transition specification."""
    n, mines = state.n, set(state.mines)
    opened, flags = dict(state.opened), set(state.flags)
    phase = state.phase
    if type(cell) is not int or not 0 <= cell < n * n:
        return state
    if operation == "flag":
        if phase != "Playing" or cell in opened:
            return state
        flags.symmetric_difference_update({cell})
    elif operation == "click":
        if phase in ("Won", "Lost") or cell in opened or cell in flags:
            return state
        if phase == "Fresh" and cell in mines:
            replacement = min(set(range(n * n)) - mines)
            mines.remove(cell)
            mines.add(replacement)
        elif phase == "Playing" and cell in mines:
            phase = "Lost"
            return board.State(n, frozenset(mines), state.opened,
                               state.flags, phase)
        frontier = deque([cell])
        while frontier:
            current = frontier.popleft()
            if current in opened or current in flags:
                continue
            if current in mines:
                raise AssertionError("independent flood hit mine")
            adjacent = [other for other in range(n * n)
                        if other != current and
                        abs(other % n - current % n) <= 1 and
                        abs(other // n - current // n) <= 1]
            clue = len(mines.intersection(adjacent))
            opened[current] = clue
            if clue == 0:
                frontier.extend(other for other in adjacent
                                if other not in opened and other not in flags
                                and other not in mines)
        phase = "Won" if len(opened) + len(mines) == n * n else "Playing"
    else:
        raise ValueError(operation)
    return board.State(n, frozenset(mines), tuple(sorted(opened.items())),
                       frozenset(flags), phase)


class NxNTransitionDifferential(unittest.TestCase):
    def test_all_three_by_three_masks_and_first_clicks(self):
        # 511 non-full mine masks times nine possible first clicks = 4599.
        for mask in range((1 << 9) - 1):
            mines = frozenset(i for i in range(9) if mask & (1 << i))
            fresh = board.new_game(3, mines)
            for cell in range(9):
                with self.subTest(mask=mask, first=cell):
                    self.assertEqual(board.click(fresh, cell),
                                     independent_step(fresh, "click", cell))

    def test_second_move_flags_and_terminal_states(self):
        # Sample mine masks systematically, including empty and near-full.
        masks = list(range(0, 511, 7)) + [0, 1, 255, 510]
        for mask in dict.fromkeys(masks):
            mines = frozenset(i for i in range(9) if mask & (1 << i))
            fresh = board.new_game(3, mines)
            for first in range(9):
                playing = board.click(fresh, first)
                for cell in range(9):
                    with self.subTest(mask=mask, first=first, cell=cell):
                        self.assertEqual(board.click(playing, cell),
                                         independent_step(playing, "click", cell))
                        marked = board.mark(playing, cell)
                        self.assertEqual(marked,
                                         independent_step(playing, "flag", cell))
                        self.assertEqual(board.click(marked, cell),
                                         independent_step(marked, "click", cell))
                        self.assertEqual(board.mark(marked, cell),
                                         independent_step(marked, "flag", cell))

    def test_invalid_inputs_and_fresh_flags_are_noops(self):
        fresh = board.new_game(3, frozenset({0, 4}))
        for cell in (-1, 9, 15, False, True, 1.0, "1"):
            self.assertIs(board.click(fresh, cell), fresh)
            self.assertIs(board.mark(fresh, cell), fresh)
        for cell in range(9):
            self.assertIs(board.mark(fresh, cell), fresh)


if __name__ == "__main__":
    unittest.main()
