"""Independent finite oracle for the N=10 teaching traces in chapters 21-22.

This checks the expected explanation, not the Bend implementation. Bend execution
is checked separately by test_nxn_playthrough.py/test_nxn_zero_inference.py.
"""
from collections import deque
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def adjacent(n: int, index: int) -> tuple[int, ...]:
    y, x = divmod(index, n)
    return tuple(sorted(
        yy * n + xx
        for yy in range(max(0, y - 1), min(n, y + 2))
        for xx in range(max(0, x - 1), min(n, x + 2))
        if (yy, xx) != (y, x)
    ))


def reveal(n: int, mines: set[int], start: int) -> set[int]:
    opened: set[int] = set()
    queue = deque([start])
    while queue:
        p = queue.popleft()
        if p in opened or p in mines:
            continue
        opened.add(p)
        if not any(q in mines for q in adjacent(n, p)):
            queue.extend(adjacent(n, p))
    return opened


class TestNxNReaderBridge(unittest.TestCase):
    def test_corner_zero_has_exactly_three_neighbors(self):
        self.assertEqual(adjacent(10, 0), (1, 10, 11))
        self.assertEqual(adjacent(10, 99), (88, 89, 98))

    def test_wall_replay_reveals_fifty_then_ninety(self):
        mines = set(range(50, 60))
        top = reveal(10, mines, 0)
        self.assertEqual(len(top), 50)
        self.assertEqual(top, set(range(50)))
        bottom = reveal(10, mines, 99)
        self.assertEqual(len(bottom), 40)
        self.assertEqual(bottom, set(range(60, 100)))
        self.assertEqual(len(top | bottom), 100 - len(mines))
        self.assertFalse((top | bottom) & mines)

    def test_manuscript_links_to_real_bend_sources(self):
        tex = (ROOT / "intermediate" / "Intermediate_Textbook.tex").read_text()
        self.assertIn("10×10でも同じゲームの規則を使う", tex)
        self.assertIn("10×10の数字0から確実な一手を探す", tex)
        self.assertIn("nxn_playthrough.bend", tex)
        self.assertIn("nxn_zero_inference.bend", tex)
        for name in ("nxn_geometry.bend", "nxn_neighbors.bend", "nxn_zero_inference.bend", "nxn_playthrough.bend"):
            self.assertTrue((ROOT / "intermediate" / "minesweeper" / name).is_file())


if __name__ == "__main__":
    unittest.main()
