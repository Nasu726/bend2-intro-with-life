#!/usr/bin/env python3
"""Contract tests for the bounded 4x4 public solver Bend oracle harness."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "test_public_solver.py"
SPEC = importlib.util.spec_from_file_location("public_solver_oracle_harness", SCRIPT)
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


class PublicSolverBatchContract(unittest.TestCase):
    def test_all_49_cases_are_preserved_in_bounded_batches(self):
        items = HARNESS.cases()
        batches = list(HARNESS.batches(items))
        self.assertEqual(len(items), 49)
        self.assertEqual(len(batches), 13)
        self.assertEqual([start for start, _ in batches], list(range(0, 49, 4)))
        self.assertEqual([item for _, batch in batches for item in batch], items)
        self.assertTrue(all(1 <= len(batch) <= 4 for _, batch in batches))
        with self.assertRaises(ValueError):
            list(HARNESS.batches(items, size=0))

    def test_each_generated_bend_program_checks_its_entire_batch(self):
        for start, batch in HARNESS.batches(HARNESS.cases()):
            with self.subTest(start=start):
                source = HARNESS.program(batch)
                self.assertEqual(source.count("def check_"), len(batch))
                self.assertEqual(source.count("Solver.provably_safe("), len(batch))
                self.assertIn("def main() -> U32:", source)

    def test_main_executes_all_batches_without_bend_installed(self):
        counts = []

        def fake_run(args, **kwargs):
            self.assertEqual(args[0], "bend")
            self.assertEqual(kwargs["timeout"], 120)
            source = Path(args[1]).read_text(encoding="utf-8")
            count = source.count("def check_")
            self.assertTrue(1 <= count <= 4)
            counts.append(count)
            return SimpleNamespace(returncode=0, stdout=f"{count}\n", stderr="")

        with patch.object(HARNESS.subprocess, "run", side_effect=fake_run):
            HARNESS.main()
        self.assertEqual(counts, [4] * 12 + [1])
        self.assertEqual(sum(counts), 49)


if __name__ == "__main__":
    unittest.main()
