"""End-to-end finite witness checks and honest failure classification."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_generated_nxn import main, run
from nxn_candidate_generator import Certificate, Generation
from verify_nxn_certificate import Audit


class GeneratedWitnessAudit(unittest.TestCase):
    def test_documented_witness_is_independently_verified(self):
        result = run()
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["generation_status"], "accepted")
        self.assertEqual(result["examined"], 3)
        self.assertEqual(result["possible"], 105)
        self.assertEqual(result["mines"], [1, 4])
        self.assertEqual(result["clicks"], [0, 2, 3])
        self.assertEqual(result["opened_count"], 14)
        self.assertEqual(result["audit_checked_clicks"], 3)

    def test_no_match_and_budget_are_not_verified(self):
        no_match = run(2, 1, 0)
        self.assertEqual(no_match["status"], "no_match")
        self.assertNotIn("audit_status", no_match)
        budget = run(4, 2, 0, max_candidates=1)
        self.assertEqual(budget["status"], "budget")
        self.assertNotIn("audit_status", budget)

    def test_audit_limit_is_not_a_success(self):
        result = run(max_hypotheses=1)
        self.assertEqual(result["generation_status"], "accepted")
        self.assertEqual(result["status"], "audit_limit")
        self.assertEqual(result["audit_reason"], "hypothesis budget")

    def test_reject_forged_witness_even_when_generator_claims_accepted(self):
        forged = Generation("accepted", 1, 105, 0, 0,
                            Certificate((1, 4), (0, 3, 2), 14))
        with patch("audit_generated_nxn.generate", return_value=forged):
            result = run()
        self.assertEqual(result["status"], "audit_invalid")
        self.assertEqual(result["audit_status"], "invalid")

    def test_explicit_invalid_audit_is_error_exit(self):
        accepted = Generation("accepted", 1, 1, 0, 0,
                              Certificate((), (0,), 4))
        with patch("audit_generated_nxn.generate", return_value=accepted), \
             patch("audit_generated_nxn.audit", return_value=Audit("invalid")), \
             redirect_stdout(StringIO()) as out:
            self.assertEqual(main([]), 3)
        self.assertEqual(json.loads(out.getvalue())["status"], "audit_invalid")

    def test_cli_json_and_exit_codes(self):
        for args, expected_code, expected_status in (
            ([], 0, "verified"),
            (["--size", "2", "--mine-count", "1"], 2, "no_match"),
            (["--max-hypotheses", "1"], 2, "audit_limit"),
        ):
            with self.subTest(args=args), redirect_stdout(StringIO()) as out:
                self.assertEqual(main(args), expected_code)
            self.assertEqual(json.loads(out.getvalue())["status"], expected_status)

    def test_small_boards_generator_auditor_agree(self):
        checked = 0
        for n, mine_counts, firsts in ((2, range(4), range(4)),
                                       (3, (0, 1, 2, 4, 8), (0, 4, 8))):
            for mines in mine_counts:
                for first in firsts:
                    result = run(n, mines, first, max_candidates=100000)
                    self.assertIn(result["status"], ("verified", "no_match"))
                    if result["status"] == "verified":
                        self.assertEqual(result["audit_status"], "valid")
                    checked += 1
        self.assertEqual(checked, 31)

    def test_bad_input_rejected(self):
        with self.assertRaises(ValueError):
            run(1, 0, 0)
        with self.assertRaises(ValueError):
            run(4, 2, 0, max_hypotheses=0)


if __name__ == "__main__":
    unittest.main()
