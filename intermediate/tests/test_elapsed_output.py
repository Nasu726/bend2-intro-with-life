"""Clock output contract: test syntax, not host scheduling precision."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from elapsed_output import is_nat_decimal


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

    def test_example_gate_uses_the_contract(self):
        source = (ROOT / "scripts" / "test_examples.py").read_text(encoding="utf8")
        self.assertIn("from elapsed_output import is_nat_decimal", source)
        self.assertIn("if not is_nat_decimal(clock):", source)
        self.assertNotIn("1 <= int(clock) < 60000", source)
        compile(source, "test_examples.py", "exec")


if __name__ == "__main__":
    unittest.main()
