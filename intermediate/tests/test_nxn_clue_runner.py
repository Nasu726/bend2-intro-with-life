"""Test N×N Bend gate's subprocess orchestration, not the Bend compiler.

A fake runner reads the generated source and reports its check count. This
checks that the full suite is executed and failures are not swallowed.
"""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
import tempfile
import subprocess
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import test_nxn_clues
from test_nxn_clues import cases, verify


class ClueRunnerContract(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.counts = []
        self.temp = tempfile.TemporaryDirectory()
        self.game = Path(self.temp.name)
        for name in ("nxn_geometry.bend", "nxn_mine_words.bend", "nxn_clues.bend"):
            (self.game / name).write_text("# test-only stub\n", encoding="utf8")
        self.game_patch = patch.object(test_nxn_clues, "GAME", self.game)
        self.game_patch.start()

    def tearDown(self):
        self.game_patch.stop()
        self.temp.cleanup()

    def fake_bend(self, args, **kwargs):
        self.calls.append(tuple(args))
        source = Path(args[1]).read_text(encoding="utf8")
        count = source.count("bit(U32.is_eq(")
        if len(args) == 2:
            self.counts.append(count)
        return SimpleNamespace(returncode=0, stdout=f"{count}\n", stderr="")

    def test_default_executes_all_533_once(self):
        checks = cases()
        self.assertEqual(len(checks), 533)
        self.assertEqual(verify(checks, runner=self.fake_bend), 533)
        self.assertEqual(self.counts, [533])
        self.assertEqual(len(self.calls), 2)

    def test_diagnostic_batches_preserve_every_case(self):
        checks = cases()
        self.assertEqual(verify(checks, batch_size=64, runner=self.fake_bend), 533)
        self.assertEqual(self.counts, [64] * 8 + [21])
        self.assertEqual(len(self.calls), 18)

    def test_failed_execution_is_not_misreported_as_success(self):
        def wrong(args, **kwargs):
            result = self.fake_bend(args, **kwargs)
            if len(args) == 2:
                result.stdout = "532\n"
            return result
        with self.assertRaisesRegex(AssertionError, "checks 1..533: got 532, expected 533"):
            verify(cases(), runner=wrong)

    def test_empty_output_is_a_diagnostic_failure(self):
        def empty(args, **kwargs):
            result = self.fake_bend(args, **kwargs)
            if len(args) == 2:
                result.stdout = "\n"
            return result
        with self.assertRaisesRegex(AssertionError, "empty output"):
            verify(cases()[:2], runner=empty)

    def test_failed_typecheck_is_not_ignored(self):
        def failed(args, **kwargs):
            result = self.fake_bend(args, **kwargs)
            if len(args) == 3:
                result.returncode = 2
                result.stderr = "simulated type error"
            return result
        with self.assertRaisesRegex(AssertionError, "typecheck, checks 1..2: exited 2"):
            verify(cases()[:2], runner=failed)

    def test_timeout_identifies_the_failing_batch(self):
        def timeout(args, **kwargs):
            raise subprocess.TimeoutExpired(args, 240)
        with self.assertRaisesRegex(AssertionError, "typecheck, checks 1..2: timed out"):
            verify(cases()[:2], runner=timeout)

    def test_invalid_batch_sizes_are_rejected(self):
        for size in (0, -1, "64"):
            with self.subTest(size=size), self.assertRaises(ValueError):
                verify(cases()[:2], batch_size=size, runner=self.fake_bend)
        with self.assertRaises(ValueError):
            verify([], runner=self.fake_bend)


if __name__ == "__main__":
    unittest.main()
