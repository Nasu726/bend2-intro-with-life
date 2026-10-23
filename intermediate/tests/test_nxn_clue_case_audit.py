"""Independent audit of the 533 generated Bend clue assertions.

Decode each generated Bend assertion and recompute its expected clue by
enumerating the eight adjacent coordinates, independently of the generator's
full-board oracle. This is Python-only and does NOT run/typecheck Bend.
"""
from collections import Counter
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from test_nxn_clues import cases

EXPR = re.compile(
    r"bit\(U32\.is_eq\(Clues\.read_count\(Clues\.clue\((.+), (\d+)\)\), (\d+)\)\)\Z")
SIZE = re.compile(r"Mines\.new\((\d+)\)")
MINE = re.compile(r", (\d+), True\{\}\)")


def decode(expression):
    match = EXPR.fullmatch(expression)
    if match is None:
        raise ValueError(f"Unrecognized Bend assertion: {expression[:100]}")
    state, index, claimed = match.groups()
    sizes = SIZE.findall(state)
    if len(sizes) != 1:
        raise ValueError("Expected exactly one Mines.new")
    n = int(sizes[0])
    mines = tuple(map(int, MINE.findall(state)))
    if state.count("Mines.set_checked(") != len(mines):
        raise ValueError("Unknown mine mutation in generated Bend assertion")
    if any(not 0 <= mine < n*n for mine in mines):
        raise ValueError("Out-of-bounds mine in generated assertion")
    return n, mines, int(index), int(claimed)


def independent_clue(n, mines, index):
    if not 0 <= index < n*n:
        return 0
    x, y = index % n, index // n
    occupied = set(mines)
    return sum((y+dy)*n+(x+dx) in occupied
               for dy in (-1, 0, 1) for dx in (-1, 0, 1)
               if (dx or dy) and 0 <= x+dx < n and 0 <= y+dy < n)


class ClueCaseAudit(unittest.TestCase):
    def test_parser_rejects_unknown_or_invalid_mine_mutations(self):
        with self.assertRaises(ValueError):
            decode("bit(U32.is_eq(0, 0))")
        with self.assertRaises(ValueError):
            decode("bit(U32.is_eq(Clues.read_count(Clues.clue(Mines.set_checked(Mines.new(3), 0, False{}), 1)), 0))")
        with self.assertRaises(ValueError):
            decode("bit(U32.is_eq(Clues.read_count(Clues.clue(Mines.set_checked(Mines.new(3), 9, True{}), 1)), 0))")

    def test_independent_oracle_rejects_corrupt_expected_clue(self):
        original = next(s for s in cases() if decode(s)[3] == 8)
        n, mines, index, expected = decode(original)
        self.assertEqual(independent_clue(n, mines, index), 8)
        corrupted = original[:-3] + "7))"
        n, mines, index, claimed = decode(corrupted)
        self.assertNotEqual(independent_clue(n, mines, index), claimed)

    def test_all_533_expected_values_have_independent_agreement(self):
        checks = cases()
        self.assertEqual(len(checks), 533)
        self.assertEqual(len(checks), len(set(checks)))
        for expression in checks:
            with self.subTest(expression=expression[:90]):
                n, mines, index, claimed = decode(expression)
                self.assertIn(n, (2, 3, 4, 10, 17, 100))
                self.assertEqual(claimed, independent_clue(n, mines, index))

    def test_boundaries_and_clue_spectrum_are_represented(self):
        sizes = Counter()
        clues = Counter()
        invalid = Counter()
        self_mine = 0
        cross_31_32 = 0
        cross_63_64 = 0
        for expression in cases():
            n, mines, index, claimed = decode(expression)
            sizes[n] += 1
            if index >= n*n:
                invalid[n] += 1
                continue
            clues[claimed] += 1
            self_mine += index in mines
            x, y = index % n, index // n
            adjacent = {(y+dy)*n+x+dx
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                        if (dx or dy) and 0 <= x+dx < n and 0 <= y+dy < n}
            if n in (10, 17, 100):
                cross_31_32 += {31, 32}.issubset(adjacent)
                cross_63_64 += {63, 64}.issubset(adjacent)
        self.assertEqual(sizes, {2: 45, 3: 81, 4: 74, 10: 118, 17: 111, 100: 104})
        self.assertEqual(set(clues), set(range(9)))
        self.assertTrue(all(invalid[n] >= 3 for n in sizes))
        self.assertGreater(self_mine, 0)
        self.assertGreater(cross_31_32, 0)
        self.assertGreater(cross_63_64, 0)


if __name__ == "__main__":
    unittest.main()
