"""Independent, Bend-free tests for the chapter-8 clock acceptance oracle."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "test_clock_intervals.py"
spec = importlib.util.spec_from_file_location("chapter8_clock_runner", MODULE)
clock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clock)


class ClockValidatorTest(unittest.TestCase):
    def test_valid_boundaries_and_variable_waits(self):
        self.assertEqual(
            clock.validate_readings(["0", "0", "0", "10", "10", "60"], 120, 0),
            [0, 10, 50],
        )
        self.assertEqual(
            clock.validate_readings(["100", "105", "110", "141", "150", "270"], 300, 1),
            [5, 31, 120],
        )

    def test_rejects_malformed_clock_output(self):
        for lines in (
            [], ["0"] * 5, ["0"] * 7,
            ["0", "0", "0", "20", "20", "100ms"],
            ["0", "0", "0", "20", "20", "-100"],
            ["0", "0", "0", "20", "20", "１００"],
            ["0", "0", "0", "20", "20", ""],
        ):
            with self.subTest(lines=lines), self.assertRaises(AssertionError):
                clock.validate_readings(lines, 500, 2)

    def test_rejects_backward_clock_between_pairs(self):
        with self.assertRaisesRegex(AssertionError, "backwards"):
            clock.validate_readings(["100", "101", "99", "119", "120", "220"], 300, 3)

    def test_rejects_backward_clock_within_pair(self):
        with self.assertRaisesRegex(AssertionError, "backwards"):
            clock.validate_readings(["100", "99", "100", "120", "130", "230"], 300, 4)

    def test_rejects_ignored_twenty_ms_sleep(self):
        with self.assertRaisesRegex(AssertionError, "ignored"):
            clock.validate_readings(["0", "0", "0", "9", "9", "109"], 200, 5)

    def test_rejects_ignored_hundred_ms_sleep(self):
        with self.assertRaisesRegex(AssertionError, "ignored"):
            clock.validate_readings(["0", "0", "0", "20", "20", "69"], 200, 6)

    def test_rejects_impossible_process_time(self):
        with self.assertRaisesRegex(AssertionError, "incompatible"):
            clock.validate_readings(["0", "0", "0", "1000", "1000", "2000"], 100, 7)

    def test_rejects_invalid_process_clock_measurements(self):
        valid = ["0", "0", "0", "20", "20", "120"]
        for wall in (-1, float("nan"), float("inf")):
            with self.subTest(wall=wall), self.assertRaisesRegex(AssertionError, "incompatible"):
                clock.validate_readings(valid, wall, 8)

    def test_rejects_unmeasured_gap_between_pairs(self):
        # The three sleep intervals total 120 ms, but the first-to-last
        # timestamp span is 100120 ms: the old sum-only test accepted it.
        with self.assertRaisesRegex(AssertionError, "incompatible"):
            clock.validate_readings(["0", "0", "100000", "100020", "100020", "100120"], 200, 9)

    def test_rejects_noncanonical_or_oversized_nat_output(self):
        valid = ["0", "0", "0", "20", "20", "120"]
        for bad in ("00", "020", " ", "+0", "9" * 129, None, 20):
            corrupted = valid.copy()
            corrupted[3] = bad
            with self.subTest(bad=repr(bad)[:32]), self.assertRaises(AssertionError):
                clock.validate_readings(corrupted, 500, 10)


if __name__ == "__main__":
    unittest.main()
