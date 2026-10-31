"""Independent cross-process witness input contract for a future Bend producer."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_nxn_witness import MAX_BYTES, main, verify_file


class WitnessFileAudit(unittest.TestCase):
    WITNESS = {"version": 1, "size": 4, "mine_count": 2, "first": 0,
               "mines": [1, 4], "clicks": [0, 2, 3], "opened_count": 14}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "witness.json"

    def write(self, data=None):
        self.path.write_text(json.dumps(self.WITNESS if data is None else data),
                             encoding="utf-8")

    def test_documented_certificate_is_valid(self):
        self.write()
        record = verify_file(self.path)
        self.assertEqual(record["status"], "valid")
        self.assertEqual((record["checked_clicks"], record["opened_count"]), (3, 14))
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(main([str(self.path)]), 0)
        self.assertEqual(json.loads(output.getvalue()), record)

    def test_subprocess_contract(self):
        self.write()
        script = Path(__file__).resolve().parents[1] / "scripts" / "audit_nxn_witness.py"
        for args, code, status in (([], 0, "valid"),
                                   (["--max-hypotheses", "1"], 2, "limit")):
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, str(script), str(self.path), *args],
                                        capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], status)
        self.write({**self.WITNESS, "clicks": [0, 3, 2]})
        result = subprocess.run([sys.executable, str(script), str(self.path)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid")

    def test_limit_is_not_success(self):
        self.write()
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(main([str(self.path), "--max-hypotheses", "1"]), 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "limit")

    def test_forged_click_order_is_rejected(self):
        self.write({**self.WITNESS, "clicks": [0, 3, 2]})
        self.assertEqual(verify_file(self.path)["status"], "invalid")

    def test_wrong_mine_count_is_rejected_before_audit(self):
        self.write({**self.WITNESS, "mine_count": 3})
        self.assertIn("mismatch", verify_file(self.path)["reason"])

    def test_duplicate_keys_are_rejected(self):
        self.path.write_text('{"version":1,"version":1}', encoding="utf-8")
        self.assertIn("duplicate", verify_file(self.path)["reason"])

    def test_missing_or_extra_fields_are_rejected(self):
        for record in ({k: v for k, v in self.WITNESS.items() if k != "clicks"},
                       {**self.WITNESS, "trusted": True}, [self.WITNESS]):
            with self.subTest(record=record):
                self.write(record)
                self.assertEqual(verify_file(self.path)["status"], "invalid")

    def test_bool_and_non_integer_arrays_are_rejected(self):
        for record in ({**self.WITNESS, "first": False},
                       {**self.WITNESS, "mines": [True, 4]},
                       {**self.WITNESS, "clicks": [0, 2.0, 3]},
                       {**self.WITNESS, "version": 2}):
            with self.subTest(record=record):
                self.write(record)
                self.assertEqual(verify_file(self.path)["status"], "invalid")

    def test_invalid_encoding_and_nonfinite_numbers(self):
        for raw in (b'\xff', b'{"x": NaN}', b'{'):
            with self.subTest(raw=raw):
                self.path.write_bytes(raw)
                self.assertEqual(verify_file(self.path)["status"], "invalid")

    def test_size_limit_and_missing_file(self):
        self.path.write_bytes(b" " * (MAX_BYTES + 1))
        self.assertIn("large", verify_file(self.path)["reason"])
        self.path.unlink()
        self.assertEqual(verify_file(self.path)["status"], "invalid")

    def test_bad_clicks_and_mines_still_reach_independent_auditor(self):
        for record in ({**self.WITNESS, "mines": [4, 1]},
                       {**self.WITNESS, "clicks": [1, 0, 2]},
                       {**self.WITNESS, "opened_count": 13}):
            with self.subTest(record=record):
                self.write(record)
                self.assertEqual(verify_file(self.path)["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
