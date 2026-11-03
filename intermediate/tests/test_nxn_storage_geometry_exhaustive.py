"""Finite storage and coordinate checks for the planned variable-size Bend board."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
import nxn_board_oracle as board


class NxNStorageGeometryExhaustive(unittest.TestCase):
    def test_all_supported_sizes_and_storage_depths(self):
        for n in range(2, 101):
            slots = n * n
            depth = 0
            while (1 << depth) < slots:
                depth += 1
            with self.subTest(n=n):
                self.assertEqual(board.storage_depth(n), depth)
                self.assertLess(1 << (depth - 1), slots)
                self.assertLessEqual(slots, 1 << depth)

    def test_all_supported_coordinates_are_distinct(self):
        for n in range(2, 101):
            seen = set()
            for y in range(n):
                for x in range(n):
                    i = board.index(n, x, y)
                    self.assertEqual(i, y * n + x)
                    self.assertNotIn(i, seen)
                    seen.add(i)
            self.assertEqual(len(seen), n * n)

    def test_every_supported_size_has_nonwrapping_corners(self):
        for n in range(2, 101):
            with self.subTest(n=n):
                self.assertEqual(set(board.neighbors(n, 0)), {1, n, n + 1})
                self.assertEqual(set(board.neighbors(n, n - 1)),
                                 {n - 2, 2 * n - 2, 2 * n - 1})
                self.assertEqual(set(board.neighbors(n, n * n - 1)),
                                 {n * n - 2, n * n - n - 1, n * n - n - 2})
                if n > 2:
                    self.assertNotIn(n, board.neighbors(n, n - 1))


if __name__ == "__main__":
    unittest.main()
