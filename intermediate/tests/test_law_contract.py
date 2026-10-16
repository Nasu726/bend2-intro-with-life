"""Require an explicit, separately maintained law/proof/engine boundary."""
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parents[1] / "minesweeper"
NAMES = (
    "hidden_is_flagged",
    "flagged_is_hidden",
    "opened_ignores_flag",
    "flag_toggle_involution",
    "reveal_hidden",
    "reveal_flagged",
    "reveal_opened",
)

class LawDrivenContractTests(unittest.TestCase):
    def test_all_claims_have_matching_proofs(self):
        law_text = (HERE / "LAWS.bend").read_text(encoding="utf-8")
        proof_text = (HERE / "PROOF.bend").read_text(encoding="utf-8")
        self.assertIn("import ./game.bend as Game", law_text)
        self.assertIn("import ./LAWS.bend as Laws", proof_text)
        actual_laws = re.findall(r"^law (\w+):", law_text, re.M)
        actual_proofs = re.findall(r"^def Laws\.(\w+)\(", proof_text, re.M)
        self.assertEqual(actual_laws, list(NAMES))
        self.assertEqual(actual_proofs, list(NAMES))

    def test_proof_gate_cannot_be_short_circuited(self):
        for name in ("LAWS.bend", "game.bend", "PROOF.bend"):
            content = (HERE / name).read_text(encoding="utf-8")
            self.assertNotIn("@unsafe", content)
            self.assertNotIn("?TODO", content)
        self.assertIn("B-02", (HERE / "REQUIREMENTS.md").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
