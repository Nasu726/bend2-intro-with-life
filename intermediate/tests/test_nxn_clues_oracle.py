"""Independent Python checks for the Bend N x N clue test generator.

No Bend binary is needed here; successful tests do not certify Bend execution.
"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_nxn_clues import cases, check_expression, expected, neighbor_ring, program


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
    def test_masked_reads_do_not_count_wrapped_coordinates(self):
        # Model the branchless Bend step: storage bounds-checks the U32
        # linear index, then the geometric predicate masks non-neighbors.
        # For (x=0,y=1), the left candidate wraps to linear index 9 on
        # a 10x10 board; reading mine 9 must still contribute zero.
        self.assertEqual((10 + 0xffffffff) & 0xffffffff, 9)
        offsets = ((-1, -1), (0, -1), (1, -1), (-1, 0),
                   (1, 0), (-1, 1), (0, 1), (1, 1))
        rng = random.Random(20261023)
        for n in (2, 3, 4, 10, 17, 100):
            cells = n * n
            layouts = [{9} if n == 10 else {0},
                       set(rng.sample(range(cells), min(cells, 12)))]
            for mines in layouts:
                for index in (0, n - 1, n, n + 1, cells - 1):
                    x, y = index % n, index // n
                    total = 0
                    for dx, dy in offsets:
                        u, v = (x + dx) & 0xffffffff, (y + dy) & 0xffffffff
                        linear = (v * n + u) & 0xffffffff
                        present = linear < cells and linear in mines
                        near = u < n and v < n and max(abs(u - x), abs(v - y)) == 1
                        total += int(present and near)
                    self.assertEqual(total, eight_directions(n, mines, index),
                                     (n, sorted(mines), index))

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
            indices = {-4294967295, -n, -1, 0, 1, n - 1, n, n + 1,
                       cells // 2, cells - 1, 31, 32, 63, 64, 99,
                       cells, cells + 27, 4294967295}
            for index in sorted(indices):
                self.assertEqual(expected(n, mines, index),
                                 eight_directions(n, mines, index),
                                 (n, index))

    def test_randomized_all_sizes_against_independent_eight_offsets(self):
        rng = random.Random(20261022)
        comparisons = 0
        for n in range(2, 101):
            cells = n * n
            probes = {0, n - 1, n, cells - 1, min(31, cells - 1),
                      min(32, cells - 1), rng.randrange(cells)}
            for _ in range(3):
                mines = set(rng.sample(range(cells), min(cells, 12)))
                for index in probes:
                    self.assertEqual(expected(n, mines, index),
                                     eight_directions(n, mines, index),
                                     (n, sorted(mines), index))
                    comparisons += 1
        self.assertGreaterEqual(comparisons, 1000)

    def test_dense_neighbor_rings_reach_high_clue_values(self):
        for n in (2, 3, 4, 10, 17, 100):
            corner = neighbor_ring(n, 0)
            self.assertEqual(len(corner), 3)
            self.assertEqual(expected(n, set(corner), 0), 3)
            self.assertEqual(expected(n, set(corner[1:]), 0), 2)
            center = n + 1
            ring = neighbor_ring(n, center)
            maximum = 3 if n == 2 else 8
            self.assertEqual(len(ring), maximum)
            self.assertNotIn(center, ring)
            self.assertEqual(expected(n, set(ring), center), maximum)
            self.assertEqual(expected(n, set(ring[1:]), center), maximum - 1)
            self.assertEqual(eight_directions(n, set(ring), center), maximum)
            self.assertEqual(eight_directions(n, set(ring[1:]), center), maximum - 1)
        checks = cases()
        self.assertTrue(any(', 8))' in check for check in checks))
        self.assertTrue(any(', 7))' in check for check in checks))

    def test_dense_neighbors_cross_word_boundaries(self):
        generated = set(cases())
        for n in (10, 17, 100):
            for boundary in (31, 63):
                focus = boundary + n
                ring = neighbor_ring(n, focus)
                self.assertEqual(len(ring), 8)
                self.assertTrue({boundary, boundary + 1}.issubset(ring))
                self.assertEqual(expected(n, set(ring), focus), 8)
                self.assertEqual(eight_directions(n, set(ring), focus), 8)
                self.assertIn(check_expression(n, ring, focus), generated)

    def test_every_clue_value_and_center_mine_exclusion(self):
        generated = set(cases())
        for n in (3, 10):
            focus = n + 1
            ring = neighbor_ring(n, focus)
            self.assertEqual(len(ring), 8)
            for k in range(9):
                neighbors = set(ring[:k])
                with_center = neighbors | {focus}
                self.assertEqual(expected(n, neighbors, focus), k)
                self.assertEqual(expected(n, with_center, focus), k)
                self.assertEqual(eight_directions(n, neighbors, focus), k)
                self.assertEqual(eight_directions(n, with_center, focus), k)
                # Both scenarios must reach the generated Bend gate, not
                # merely pass the Python-only independent oracle.
                self.assertIn(check_expression(n, neighbors, focus), generated)
                self.assertIn(check_expression(n, with_center, focus), generated)

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
