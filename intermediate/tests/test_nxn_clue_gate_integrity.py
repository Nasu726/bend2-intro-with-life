"""Check that every finite N×N clue oracle assertion reaches Bend main.

These are Python-only generator integrity tests. They do not execute Bend;
`intermediate/scripts/test_nxn_geometry.py` performs that separate gate.
"""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_nxn_clues import cases, program


class ClueGateIntegrity(unittest.TestCase):
    def check_wiring(self, checks, source=None):
        if source is None:
            source = program(checks)
        groups = re.findall(
            r"^def group_(\d+)\(\) -> U32:\n  \(([^\n]*) : U32\)$",
            source, re.MULTILINE,
        )
        expected_offsets = list(range(0, len(checks), 3))
        self.assertEqual([int(offset) for offset, _ in groups], expected_offsets)

        # Each group must contain exactly its assigned finite comparisons.
        for (offset, body) in groups:
            chunk = checks[int(offset):int(offset) + 3]
            self.assertEqual(body, " + ".join(chunk))
            self.assertEqual(body.count("bit(U32.is_eq("), len(chunk))

        main = source.split("def main() -> U32:\n  (", 1)
        self.assertEqual(len(main), 2)
        self.assertTrue(main[1].endswith(" : U32)\n"))
        calls = re.findall(r"group_(\d+)\(\)", main[1])
        self.assertEqual([int(offset) for offset in calls], expected_offsets)
        self.assertEqual(main[1],
                         " + ".join(f"group_{i}()" for i in expected_offsets)
                         + " : U32)\n")

    def test_partial_groups_are_not_dropped(self):
        # A final group of one or two assertions must also reach main.
        sample = cases()[:5]
        for count in (1, 2, 3, 4, 5):
            with self.subTest(count=count):
                self.check_wiring(sample[:count])

    def test_all_533_assertions_reach_main_once(self):
        checks = cases()
        self.assertEqual(len(checks), 533)
        self.assertEqual(len(set(checks)), len(checks))
        self.check_wiring(checks)

    def test_missing_comparison_and_duplicate_call_are_rejected(self):
        checks = cases()[:4]
        source = program(checks)
        omitted = source.replace(" + ".join(checks[:3]),
                                 " + ".join(checks[:2]), 1)
        self.assertNotEqual(omitted, source)
        with self.assertRaises(AssertionError):
            self.check_wiring(checks, omitted)

        prefix, main = source.split("def main() -> U32:\n  (", 1)
        duplicated = prefix + "def main() -> U32:\n  (" + main.replace(
            "group_3()", "group_0()", 1)
        self.assertNotEqual(duplicated, source)
        with self.assertRaises(AssertionError):
            self.check_wiring(checks, duplicated)


if __name__ == "__main__":
    unittest.main()
