"""Python generator contract, separate from the actual Bend execution gate."""
from pathlib import Path
import re
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_nxn_public_state import cases, program, verify


class PublicStateGeneratorTests(unittest.TestCase):
    def test_replay_frames_and_boundary_sizes_are_covered(self):
        checks = cases()
        self.assertEqual(len(checks), 19)
        self.assertEqual([name for name, *_ in checks[:13]],
                         [f"frame_{i}" for i in range(13)])
        self.assertEqual([name for name, *_ in checks[13:]],
                         [f"boundary_{n}" for n in (2, 3, 4, 10, 17, 100)])
        self.assertEqual(sum(len(actions) for _, _, _, actions, _ in checks[:13]), 90)
        self.assertTrue(all(len(reads) >= 7 for _, _, _, _, reads in checks))

    def test_every_check_is_wired_to_main_once(self):
        checks = cases()
        source, total = program(checks)
        self.assertGreater(total, 250)
        self.assertEqual(total, sum(len(reads) + 1
                                    for _, _, _, _, reads in checks) + 10)
        self.assertEqual(source.count("= check_total("), len(checks))
        self.assertEqual(len(re.findall(r"^def check_\w+\(\) -> U32:$", source, re.M)), 20)
        self.assertEqual(len(re.findall(r"^  p\d+ = check_one\(", source, re.M)),
                         total - len(checks) - 10)
        main = source.split("def main() -> U32:\n", 1)[1]
        self.assertEqual(main.count("check_"), 20)
        for name, *_ in checks:
            self.assertEqual(main.count(f"check_{name}()"), 1)
        self.assertEqual(main.strip(),
                         "(" + " + ".join(f"check_{name}()" for name, *_ in checks)
                         + " + check_config() : U32)")

    def test_duplicate_reveal_keeps_first_clue_and_invalid_reads_are_hidden(self):
        for name, _, _, actions, reads in cases()[13:]:
            self.assertEqual(actions[:2], [(0, 8), (0, 1)])
            self.assertEqual(dict(reads)[0], 8)
            self.assertEqual(dict(reads)[4294967295], 9)
            self.assertEqual(dict(reads)[int(name.split("_")[-1])**2], 9)

    def test_m_is_independent_of_n(self):
        checks = cases()
        self.assertEqual(checks[0][1], "Public.new(10, 10)")
        boundary = {name: (initial, mines)
                    for name, initial, mines, _, _ in checks[13:]}
        self.assertEqual(boundary["boundary_2"], ("Public.new(2, 0)", 0))
        self.assertEqual(boundary["boundary_10"], ("Public.new(10, 99)", 99))
        self.assertEqual(boundary["boundary_100"], ("Public.new(100, 9999)", 9999))
        source, _ = program(checks)
        self.assertIn("Public.total_mines(board)", source)
        self.assertIn("Public.valid_config(10, 100)", source)

    def test_runner_rejects_extra_stdout(self):
        class Fake:
            def __init__(self):
                self.calls = 0
            def __call__(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                return SimpleNamespace(returncode=0, stdout="123\nnoise\n", stderr="")
        with self.assertRaisesRegex(AssertionError, "mismatch"):
            verify(runner=Fake())


if __name__ == "__main__":
    unittest.main()
