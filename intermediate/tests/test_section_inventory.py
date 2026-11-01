"""Bend-free coverage of the editorial section inventory."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_section_flow", ROOT / "scripts" / "audit_section_flow.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class EditorialInventoryTest(unittest.TestCase):
    def test_nested_exercise_body(self):
        self.assertEqual(audit.command_bodies(r"\exercise{\code{Map.get}を試してみましょう。}", "exercise"),
                         [r"\code{Map.get}を試してみましょう。"])

    def test_unclosed_exercise_rejected(self):
        with self.assertRaises(ValueError):
            audit.command_bodies(r"\exercise{\code{bad}", "exercise")

    def test_target_ending_is_at_the_end(self):
        self.assertTrue(audit.target_ending("試してみましょう。"))
        self.assertFalse(audit.target_ending("試してみましょう。結果を説明しましょう。"))

    def test_section_scope_missing_sample(self):
        text = (r"\chapter{A}" + "\n" + r"\section{one}\sample{a.bend}\exercise{試してみましょう。}" +
                "\n" + r"\section{two}" + "\n" + r"\begin{lstlisting}" + "\n" +
                r"\chapter{B}" + "\n" + r"\section{third}\sample{missing.bend}\exercise{予想しましょう。}")
        rows, missing = audit.inventory(text, {"a.bend"})
        self.assertEqual([x["sections"] for x in rows], [2, 1])
        self.assertEqual([x["code_sections"] for x in rows], [2, 1])
        self.assertEqual([x["ending_review"] for x in rows], [0, 1])
        self.assertEqual(missing, ["missing.bend"])


    def test_review_locations_and_nested_braces(self):
        text = (r"\chapter{One}" + "\n" +
                r"\section{S1}\exercise{\code{Map.has}を予想しましょう。}" + "\n" +
                r"\section{S2}\exercise{結果を試してみましょう。}" + "\n" +
                r"\chapter{Two}" + "\n" +
                r"\section{S3}GUIはまだ統合していません。")
        details = audit.review_details(text)
        self.assertEqual([(d["chapter"], d["section"], d["line"], d["kind"])
                          for d in details],
                         [(1, "S1", 2, "exercise_ending"),
                          (2, "S3", 5, "stale_gui_status")])

    def test_review_not_a_publication_gate(self):
        text = (r"\chapter{One}" + "\n" +
                r"\section{S}\exercise{結果を調べてみましょう。}")
        self.assertEqual(audit.review_details(text), [])

    def test_review_unclosed_exercise_is_error(self):
        with self.assertRaises(ValueError):
            audit.review_details(r"\chapter{A}\exercise{broken")

    def test_actual_reader_samples_resolve(self):
        text = (ROOT / "Intermediate_Textbook.tex").read_text(encoding="utf-8")
        files = {p.name for p in (ROOT / "src").glob("*.bend")}
        rows, missing = audit.inventory(text, files)
        self.assertEqual(len(rows), 23)
        self.assertEqual(missing, [])
        self.assertGreater(sum(row["sections"] for row in rows), 23)
        self.assertGreater(sum(row["exercises"] for row in rows), 0)


if __name__ == "__main__":
    unittest.main()
