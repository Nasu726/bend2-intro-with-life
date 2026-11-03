"""Keep the expensive N x N Bend oracle independent of the 180-second wrapper."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClueCiContract(unittest.TestCase):
    def test_case_count_and_boundary_sizes(self):
        path = ROOT / "scripts" / "test_nxn_clues.py"
        spec = importlib.util.spec_from_file_location("nxn_clue_oracle", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        boards = module.build_cases()
        self.assertEqual(sum(len(indices) for _, _, indices in boards), 510)
        self.assertEqual({n for n, _, _ in boards}, {2, 3, 4, 10, 17, 100})
        self.assertTrue(all(n*n in indices and 2**32-1 in indices
                            for n, _, indices in boards))

    def test_expensive_oracle_is_not_nested_in_short_timeout(self):
        examples = (ROOT / "scripts" / "test_examples.py").read_text(encoding="utf-8")
        workflow = (ROOT.parent / ".github" / "workflows" / "intermediate.yml").read_text(encoding="utf-8")
        self.assertNotIn('run(sys.executable, str(ROOT / "scripts" / "test_nxn_clues.py"))', examples)
        self.assertIn("run: python3 intermediate/scripts/test_nxn_clues.py", workflow)
        self.assertIn("run: python3 intermediate/scripts/test_examples.py", workflow)


if __name__ == "__main__":
    unittest.main()
