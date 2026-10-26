"""Strict JSON boundary and separate-process replay for single-clue proofs."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_single_clue_witness.py"
sys.path.insert(0, str(ROOT / "scripts"))
from audit_single_clue_witness import audit_document, unique_object


def witness():
    return {
        "version": 1, "size": 3,
        "opened": [[0, 0], [2, 1], [6, 1]],
        "certified_mines": [], "certified_safe": [],
        "steps": [
            {"clue": 0, "mines": [], "safe": [1, 3, 4]},
            {"clue": 2, "mines": [5], "safe": []},
            {"clue": 6, "mines": [7], "safe": []},
        ],
    }


class WitnessTests(unittest.TestCase):
    def run_cli(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "proof.json"
            path.write_bytes(data)
            process = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                     capture_output=True, text=True, timeout=15)
            return process.returncode, json.loads(process.stdout)

    def test_valid_witness_in_separate_process(self):
        result = audit_document(witness())
        self.assertEqual(result, {"status": "valid", "size": 3, "steps": 3,
                                  "mines": [5, 7], "safe": [1, 3, 4]})
        code, output = self.run_cli(json.dumps(witness()).encode())
        self.assertEqual((code, output), (0, result))

    def test_missing_and_extra_fields_fail_closed(self):
        for key in ("opened", "steps", "version"):
            doc = witness()
            del doc[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                audit_document(doc)
        doc = witness()
        doc["hidden_mines"] = [5, 7]
        with self.assertRaises(ValueError):
            audit_document(doc)

    def test_bool_and_noncanonical_cells_rejected(self):
        for key, value in (("size", True), ("version", True),
                           ("certified_mines", [True]),
                           ("certified_safe", [3, 1]),
                           ("opened", [[2, 1], [0, 0], [6, 1]]),
                           ("opened", [[0, 0], [0, 1]])):
            doc = witness()
            doc[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                audit_document(doc)

    def test_forged_and_incomplete_steps_rejected(self):
        for mutation in ("missing", "wrong", "repeated", "unrevealed"):
            doc = witness()
            if mutation == "missing":
                doc["steps"].pop()
            elif mutation == "wrong":
                doc["steps"][0]["safe"] = [1, 3, 5]
            elif mutation == "repeated":
                doc["steps"].append(copy.deepcopy(doc["steps"][0]))
            else:
                doc["steps"][0]["clue"] = 8
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                audit_document(doc)

    def test_duplicate_json_keys_and_oversize_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"size":3,"size":4}', object_pairs_hook=unique_object)
        code, result = self.run_cli(b'{"size":3,"size":4}')
        self.assertEqual((code, result["status"]), (3, "invalid"))
        code, result = self.run_cli(b" " * 65537)
        self.assertEqual((code, result["status"]), (3, "invalid"))

    def test_invalid_json_and_boolean_steps_rejected(self):
        for data in (b"{", b"\xff", b"[]"):
            with self.subTest(data=data):
                code, result = self.run_cli(data)
                self.assertEqual((code, result["status"]), (3, "invalid"))
        doc = witness()
        doc["steps"][0]["clue"] = True
        with self.assertRaises(ValueError):
            audit_document(doc)

    def test_empty_trace_with_complete_initial_evidence(self):
        doc = {"version": 1, "size": 3, "opened": [[0, 0]],
               "certified_mines": [], "certified_safe": [1, 3, 4], "steps": []}
        self.assertEqual(audit_document(doc)["safe"], [1, 3, 4])


if __name__ == "__main__":
    unittest.main()
