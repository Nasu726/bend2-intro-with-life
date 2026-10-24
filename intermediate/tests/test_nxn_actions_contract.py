"""Pure-Python structural and reference checks for the N x N action oracle."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location("nxn_actions_test", ROOT / "scripts" / "test_nxn_actions.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ActionOracleContract(unittest.TestCase):
    def test_boundaries_and_cases(self):
        m = load()
        cases = m.build_cases()
        self.assertEqual({n for n, _, _, _ in cases}, {2, 3, 4, 10, 17, 100})
        self.assertGreaterEqual(len(cases), 100)
        self.assertTrue(any(i == 2**32-1 for _, _, actions, read in cases
                            for _, i in actions))
        self.assertTrue(any(read == 2**32-1 for _, _, _, read in cases))

    def test_reference_semantics(self):
        m = load()
        self.assertEqual(m.reference(10, {1}, (("click", 0),), 0), (1, 0))
        self.assertEqual(m.reference(10, {1}, (("mark", 1), ("click", 1)), 1), (11, 0))
        self.assertEqual(m.reference(10, {1}, (("click", 1), ("click", 0)), 0), (10, 1))
        self.assertEqual(m.reference(10, {1}, (("click", 100),), 100), (12, 0))
        self.assertEqual(m.reference(10, {1}, (("click", 0), ("mark", 0)), 0), (1, 0))

    def test_generated_bend_checks_both_outputs(self):
        m = load()
        source = m.bend_source(m.build_cases())
        self.assertIn("Actions.public_at(state,", source)
        self.assertIn("Actions.lost_code(state)", source)
        self.assertIn("def main() -> U32:", source)


if __name__ == "__main__":
    unittest.main()
