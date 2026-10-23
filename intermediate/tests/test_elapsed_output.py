"""Clock output contract: test syntax, not host scheduling precision."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from elapsed_output import is_nat_decimal, is_nat_stdout


class ElapsedOutputContract(unittest.TestCase):
    def test_zero_is_valid_when_clock_resolution_is_coarse(self):
        self.assertTrue(is_nat_decimal("0"))

    def test_any_canonical_nonnegative_nat_is_valid(self):
        for value in ("1", "20", "123", "60000", "999999999999999999999"):
            with self.subTest(value=value):
                self.assertTrue(is_nat_decimal(value))

    def test_noncanonical_or_non_numeric_output_is_rejected(self):
        for value in ("", "-1", "+20", "00", "020", "20.0", "20 ms", " 20", "20 ",
                      "20\n", "20\n21", "２０", "²", "0x14", None, 20):
            with self.subTest(value=value):
                self.assertFalse(is_nat_decimal(value))

    def test_process_stdout_accepts_one_optional_line_ending(self):
        for output in ("0", "0\n", "20", "20\n", "20\r\n", "60000\n"):
            with self.subTest(output=repr(output)):
                self.assertTrue(is_nat_stdout(output))

    def test_process_stdout_rejects_hidden_extra_output(self):
        for output in ("", " ", " 20\n", "20 \n", "20\n\n",
                       "debug\n20\n", "20\nwarning", "20\r", "20\r\n\n",
                       "２０\n", "00\n", None, 20):
            with self.subTest(output=repr(output)):
                self.assertFalse(is_nat_stdout(output))

    def test_example_gate_uses_the_contract(self):
        source = (ROOT / "scripts" / "test_examples.py").read_text(encoding="utf8")
        self.assertIn("from elapsed_output import is_nat_stdout", source)
        self.assertIn("not is_nat_stdout(clock_run.stdout)", source)
        self.assertIn("clock_run.returncode != 0", source)
        self.assertNotIn('clock = run("bend", str(SAMPLES / "46_elapsed_clock.bend"))', source)
        self.assertNotIn("1 <= int(clock) < 60000", source)
        compile(source, "test_examples.py", "exec")


if __name__ == "__main__":
    unittest.main()
