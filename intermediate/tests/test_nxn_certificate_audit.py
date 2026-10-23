"""Independent finite audit of a no-guess certificate; Python reference only."""
from dataclasses import dataclass, replace
from pathlib import Path
import sys
import unittest
from itertools import combinations

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
from nxn_certificate_audit import (AuditLimit, audit_certificate,
                                   independently_forced_safe)


@dataclass(frozen=True)
class Fixture:
    width: int
    height: int
    mine_count: int
    first_click: int
    mines: frozenset[int]
    clicks: tuple[int, ...]


class IndependentAuditTests(unittest.TestCase):
    def test_10x10_ten_mine_certificate(self):
        cert = Fixture(10, 10, 10, 0,
                       frozenset({4, 29, 34, 36, 37, 49, 50, 56, 72, 77}),
                       (0, 14, 5, 6, 24, 35, 38, 39, 46, 47, 48, 57, 67))
        self.assertEqual(cert.mines, frozenset({4, 29, 34, 36, 37, 49, 50, 56, 72, 77}))
        self.assertTrue(audit_certificate(cert))
        self.assertFalse(audit_certificate(replace(cert, clicks=cert.clicks[:-1])))
        self.assertFalse(audit_certificate(replace(cert, clicks=(0, 4))))
        self.assertFalse(audit_certificate(replace(cert, clicks=(0, 99))))
        self.assertFalse(audit_certificate(replace(cert, clicks=cert.clicks + (67,))))
        self.assertFalse(audit_certificate(cert, node_limit=1))

    def test_generated_candidate_is_independently_audited(self):
        from nxn_noguess_generator import generate_no_guess_frontier
        cert = generate_no_guess_frontier(10, 10, 10, 0, seed=20261023)
        self.assertTrue(audit_certificate(cert))

    def test_independent_audit_matches_full_layout_enumeration(self):
        # Exhaust all 4x4 boards with exactly two mines for several public
        # observations. Enumerate candidate hidden placements directly; the
        # production solver is not called to obtain expected safe cells.
        from nxn_certificate_audit import _neighbors
        for mines in combinations(range(16), 2):
            mines = frozenset(mines)
            for opened_cell in (0, 5, 10, 15):
                if opened_cell in mines:
                    continue
                clue = sum(i in mines for i in _neighbors(opened_cell, 4, 4))
                opened = {opened_cell: clue}
                compatible = [frozenset(layout)
                              for layout in combinations(
                                  (i for i in range(16) if i != opened_cell), 2)
                              if sum(i in layout for i in _neighbors(opened_cell, 4, 4)) == clue]
                self.assertTrue(compatible)
                for click in range(16):
                    if click == opened_cell:
                        continue
                    expected = all(click not in layout for layout in compatible)
                    self.assertEqual(independently_forced_safe(
                        4, 4, 2, opened, click), expected,
                        (mines, opened_cell, click))

    def test_rejects_contradictions_and_budget_exhaustion(self):
        with self.assertRaises(ValueError):
            independently_forced_safe(2, 2, 1, {0: 3}, 1)
        with self.assertRaises(ValueError):
            independently_forced_safe(2, 2, 1, {0: 0, 1: 1}, 2)
        with self.assertRaises(ValueError):
            independently_forced_safe(4, 4, 2, {0: 0}, 0)
        with self.assertRaises(AuditLimit):
            independently_forced_safe(10, 10, 10, {0: 0}, 14, node_limit=1)
        for invalid in ({0: True}, {-1: 0}, {0: 9}):
            with self.assertRaises(ValueError):
                independently_forced_safe(4, 4, 2, invalid, 1)

    def test_independent_audit_rejects_malformed_certificate(self):
        valid = Fixture(2, 2, 0, 0, frozenset(), (0,))
        self.assertTrue(audit_certificate(valid))
        for invalid in (
            replace(valid, width=True),
            replace(valid, mine_count=True),
            replace(valid, mines=frozenset({True})),
            replace(valid, clicks=(True,)),
            replace(valid, clicks=(0, 0)),
            replace(valid, clicks=(1,)),
        ):
            self.assertFalse(audit_certificate(invalid))
        self.assertFalse(audit_certificate(None))


if __name__ == "__main__":
    unittest.main()
