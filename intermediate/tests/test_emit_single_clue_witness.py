"""Reference JSON producer to separate-process checker round-trip."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emit_single_clue_witness.py"
AUDIT = ROOT / "scripts" / "audit_single_clue_witness.py"
sys.path.insert(0, str(ROOT / "scripts"))
from emit_single_clue_witness import produce


def public_evidence():
    return {"version": 1, "size": 3, "opened": [[0, 0], [2, 1], [6, 1]],
            "certified_mines": [], "certified_safe": []}


class EmitWitnessTests(unittest.TestCase):
    def run_emit(self, evidence):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "public.json"
            dst = Path(folder) / "proof.json"
            src.write_bytes(evidence)
            producer = subprocess.run([sys.executable, str(SCRIPT), str(src), str(dst)],
                                      capture_output=True, text=True, timeout=15)
            if producer.returncode != 0:
                return producer.returncode, json.loads(producer.stdout), None
            checker = subprocess.run([sys.executable, str(AUDIT), str(dst)],
                                     capture_output=True, text=True, timeout=15)
            self.assertEqual(checker.returncode, 0, checker.stdout + checker.stderr)
            return producer.returncode, json.loads(producer.stdout), json.loads(checker.stdout)

    def test_complete_three_clue_round_trip(self):
        code, produced, checked = self.run_emit(json.dumps(public_evidence()).encode())
        self.assertEqual(code, 0)
        self.assertEqual(produced["steps"], 3)
        self.assertEqual((checked["mines"], checked["safe"]), ([5, 7], [1, 3, 4]))
        self.assertEqual(produce(public_evidence())["steps"], [
            {"clue": 0, "mines": [], "safe": [1, 3, 4]},
            {"clue": 2, "mines": [5], "safe": []},
            {"clue": 6, "mines": [7], "safe": []},
        ])

    def test_empty_fixed_point_and_initial_evidence(self):
        doc = {"version": 1, "size": 3, "opened": [[0, 0]],
               "certified_mines": [], "certified_safe": [1, 3, 4]}
        self.assertEqual(produce(doc)["steps"], [])
        code, _, checked = self.run_emit(json.dumps(doc).encode())
        self.assertEqual((code, checked["safe"]), (0, [1, 3, 4]))

    def test_noncanonical_and_false_evidence_rejected(self):
        for key, value in (("size", True), ("version", 2),
                           ("opened", [[2, 1], [0, 0], [6, 1]]),
                           ("opened", [[0, 0], [0, 1]]),
                           ("certified_mines", [True]),
                           ("certified_safe", [4, 3])):
            doc = public_evidence()
            doc[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                produce(doc)
        doc = public_evidence()
        doc["hidden_mines"] = [5, 7]
        with self.assertRaises(ValueError):
            produce(doc)

    def test_duplicate_json_keys_and_oversized_input(self):
        for raw in (b'{"size":3,"size":4}', b" " * 65537, b"\xff"):
            with self.subTest(raw=raw[:30]):
                code, result, checked = self.run_emit(raw)
                self.assertEqual((code, result["status"], checked), (3, "invalid", None))

    def test_local_contradiction_rejected(self):
        doc = {"version": 1, "size": 3, "opened": [[0, 8]],
               "certified_mines": [], "certified_safe": []}
        with self.assertRaises(ValueError):
            produce(doc)

    def test_never_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "public.json"
            dst = Path(folder) / "proof.json"
            src.write_text(json.dumps(public_evidence()), encoding="utf-8")
            dst.write_text("keep", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(src), str(dst)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 3)
            self.assertEqual(dst.read_text(), "keep")

    def test_deterministic_wire_format(self):
        raw = json.dumps(public_evidence()).encode()
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "public.json"
            src.write_bytes(raw)
            outputs = []
            for i in range(2):
                dst = Path(folder) / f"proof-{i}.json"
                result = subprocess.run([sys.executable, str(SCRIPT), str(src), str(dst)],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                outputs.append(dst.read_bytes())
            self.assertEqual(*outputs)


if __name__ == "__main__":
    unittest.main()
