"""Bend-free adversarial tests for the chapter-7 byte-content oracle."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "test_byte_file_chunks.py"
spec = importlib.util.spec_from_file_location("chapter7_byte_runner", MODULE)
byte_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(byte_runner)


def oracle(payload: bytes, reads: int = 6) -> list[str]:
    result = []
    for offset in range(0, reads * 2, 2):
        chunk = payload[offset:offset + 2]
        value = 0
        for digit in chunk:
            value = 257 * value + digit + 1
        result.extend((str(len(chunk)), str(value)))
    return result


class ByteChunkValidatorTest(unittest.TestCase):
    def test_accepts_all_lengths_and_content_families(self):
        families = (bytes(range(16)), bytes([0, 10, 255, 13, 0, 7, 8, 9, 10, 11, 12, 13, 14, 15]), bytes([255] * 16))
        for family in families:
            for size in range(17):
                with self.subTest(size=size, family=family[:2]):
                    byte_runner.validate_chunk_output(family[:size], oracle(family[:size]))

    def test_known_nonpalindromic_digest(self):
        payload = bytes((0, 10, 255))
        byte_runner.validate_chunk_output(payload, ["2", "268", "1", "256"] + ["0", "0"] * 4)
        self.assertNotEqual(oracle(bytes((10, 0))), oracle(bytes((0, 10))))

    def test_rejects_reordered_bytes_of_same_length(self):
        payload = bytes((0, 10))
        with self.assertRaisesRegex(AssertionError, "Expected"):
            byte_runner.validate_chunk_output(payload, oracle(bytes((10, 0))))

    def test_rejects_wrong_content_in_later_chunk(self):
        payload = bytes((0, 10, 255, 13, 42, 1))
        corrupted = oracle(payload)
        corrupted[5] = str(int(corrupted[5]) + 1)
        with self.assertRaises(AssertionError):
            byte_runner.validate_chunk_output(payload, corrupted)

    def test_rejects_premature_eof(self):
        payload = bytes(range(11))
        corrupted = oracle(payload)
        corrupted[10:12] = ["0", "0"]
        with self.assertRaises(AssertionError):
            byte_runner.validate_chunk_output(payload, corrupted)

    def test_rejects_wrong_chunk_length(self):
        corrupted = oracle(b"a")
        corrupted[0] = "2"
        with self.assertRaises(AssertionError):
            byte_runner.validate_chunk_output(b"a", corrupted)

    def test_rejects_missing_or_extra_lines(self):
        valid = oracle(b"abc")
        for bad in (valid[:-1], valid + ["0"], []):
            with self.subTest(bad=bad), self.assertRaises(AssertionError):
                byte_runner.validate_chunk_output(b"abc", bad)

    def test_rejects_noncanonical_output(self):
        valid = oracle(b"abc")
        for bad in ("", "-1", "+1", "１", " 2", "2 ", "02", "999999", "2.0", None, 3):
            corrupted = valid.copy()
            corrupted[0] = bad
            with self.subTest(bad=bad), self.assertRaises(AssertionError):
                byte_runner.validate_chunk_output(b"abc", corrupted)

    def test_accepts_seventh_read_to_distinguish_twelve_from_thirteen(self):
        payload = bytes(range(13))
        byte_runner.validate_chunk_output(payload, oracle(payload, reads=7), reads=7)
        self.assertNotEqual(oracle(payload[:12], reads=7), oracle(payload, reads=7))

    def test_stdout_accepts_one_terminal_newline(self):
        payload = b"abc"
        raw = "\n".join(oracle(payload))
        for stdout in (raw, raw + "\n"):
            with self.subTest(terminal_lf=stdout.endswith("\n")):
                byte_runner.validate_chunk_output(
                    payload, byte_runner.parse_stdout_lines(stdout)
                )

    def test_stdout_rejects_extra_lines_padding_and_nonstrings(self):
        payload = b"abc"
        raw = "\n".join(oracle(payload))
        for stdout in (
            "\n" + raw, raw + "\n\n", raw + "\n ",
            " " + raw, raw + " ", raw + "\r\n", None,
        ):
            with self.subTest(stdout=repr(stdout)[:48]), self.assertRaises(AssertionError):
                byte_runner.validate_chunk_output(
                    payload, byte_runner.parse_stdout_lines(stdout)
                )

    def test_rejects_nonpositive_read_count(self):
        for reads in (0, -1):
            with self.assertRaises(ValueError):
                byte_runner.validate_chunk_output(b"", [], reads=reads)


if __name__ == "__main__":
    unittest.main()
