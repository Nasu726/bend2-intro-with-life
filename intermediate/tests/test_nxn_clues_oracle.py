"""Independent Python checks for the Bend N x N clue test generator.

No Bend binary is needed here; successful tests do not certify Bend execution.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_nxn_clues import cases, expected, program


def eight_directions(n, mines, index):
    """Count via eight coordinate offsets, not a full-board scan."""
    if not 0 <= index < n * n:
        return 0
    x, y = index % n, index // n
    count = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            xx, yy = x + dx, y + dy
            if 0 <= xx < n and 0 <= yy < n:
                count += int(yy * n + xx in mines)
    return count


class ClueOracleContract(unittest.TestCase):
    def test_exhaustive_two_and_three_square_boards(self):
        comparisons = 0
        for n in (2, 3):
            cells = n * n
            for mask in range(1 << cells):
                mines = {i for i in range(cells) if mask & (1 << i)}
                for index in range(cells):
                    self.assertEqual(expected(n, mines, index),
                                     eight_directions(n, mines, index),
                                     (n, mask, index))
                    comparisons += 1
        self.assertEqual(comparisons, 4672)

    def test_all_sizes_boundaries_and_invalid_indices(self):
        for n in range(2, 101):
            cells = n * n
            mines = {i for i in (0, 1, n - 1, n, n + 1, 31, 32, 63, 64,
                                 99, cells - 1) if i < cells}
            indices = {0, 1, n - 1, n, n + 1, cells // 2, cells - 1,
                       31, 32, 63, 64, 99, cells, cells + 27, 4294967295}
            for index in sorted(indices):
                self.assertEqual(expected(n, mines, index),
                                 eight_directions(n, mines, index),
                                 (n, index))

    def test_generator_is_deterministic_and_has_a_main(self):
        checks = cases()
        self.assertGreater(len(checks), 400)
        self.assertEqual(checks, cases())
        self.assertEqual(len(checks), len(set(checks)))
        source = program(checks)
        self.assertIn('def main() -> U32:', source)
        self.assertIn('import ./nxn_clues.bend as Clues', source)
        self.assertIn('4294967295', source)
        self.assertIn('Mines.new(100)', source)
        self.assertIn('Mines.new(2)', source)


if __name__ == '__main__':
    unittest.main()
