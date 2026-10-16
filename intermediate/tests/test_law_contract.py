"""Check law/proof/engine boundaries, including the finite board milestone."""
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
    "board_top_edge_adjacent",
    "board_corner_diagonal",
    "board_no_wrap",
    "board_no_self_neighbor",
    "board_outside_x",
    "board_toggle_keeps_mine",
    "board_safe_reveal_keeps_mine",
    "board_reveal_monotone_on_open",
    "board_safe_reveal_keeps_flag",
    "board4_toggle_keeps_all_mines",
    "board4_reveal_keeps_all_mines",
    "board4_empty_clue_is_zero",
    "board4_own_mine_not_counted",
    "board4_diagonal_clue",
    "board4_two_mines_clue",
    "board4_rejects_invalid_flag_index",
    "board4_rejects_invalid_reveal_index",
)

class LawDrivenContractTests(unittest.TestCase):
    def test_all_claims_have_matching_proofs(self):
        law_text = (HERE / "LAWS.bend").read_text(encoding="utf-8")
        proof_text = (HERE / "PROOF.bend").read_text(encoding="utf-8")
        self.assertIn("import ./game.bend as Game", law_text)
        self.assertIn("import ./board.bend as Board", law_text)
        self.assertIn("import ./board4.bend as Board4", law_text)
        self.assertIn("import ./LAWS.bend as Laws", proof_text)
        actual_laws = re.findall(r"^law (\w+):", law_text, re.M)
        actual_proofs = re.findall(r"^def Laws\.(\w+)\(", proof_text, re.M)
        self.assertEqual(actual_laws, list(NAMES))
        self.assertEqual(actual_proofs, list(NAMES))

    def test_proof_gate_cannot_be_short_circuited(self):
        for name in ("LAWS.bend", "game.bend", "board.bend", "board4.bend", "PROOF.bend"):
            content = (HERE / name).read_text(encoding="utf-8")
            self.assertNotIn("@unsafe", content)
            self.assertNotIn("?TODO", content)
        ledger = (HERE / "REQUIREMENTS.md").read_text(encoding="utf-8")
        self.assertIn("B-02", ledger)
        self.assertIn("B-04", ledger)

if __name__ == "__main__":
    unittest.main()
