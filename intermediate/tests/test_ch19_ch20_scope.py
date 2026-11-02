"""Static chapter 19-20 editorial contract; runtime evidence is separate."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def chapter(number):
    source = text("Intermediate_Textbook.tex")
    parts = re.split(r"(?=^\\chapter\{)", source, flags=re.MULTILINE)
    chapters = [p for p in parts if p.startswith(r"\chapter{")]
    return chapters[number - 1]


class ParallelAndTargetScopeTest(unittest.TestCase):
    def test_section_counts(self):
        self.assertEqual(len(re.findall(r"^\\section\{", chapter(19), re.M)), 6)
        self.assertEqual(len(re.findall(r"^\\section\{", chapter(20), re.M)), 8)

    def test_balanced_tree_is_not_a_gpu_benchmark(self):
        body = chapter(19)
        self.assertIn("count_leaves(8n)", text("src/06_parallel.bend"))
        self.assertIn("256", body)
        self.assertIn("特定のGPUでの速度向上までは測定していません", body)

    def test_io_fork_is_not_cpu_parallelism(self):
        body = chapter(19)
        source = text("src/21_io_fork.bend")
        self.assertIn("IO.fork(U32, IO.pure(U32, 7))", source)
        self.assertIn("IO.join(U32, chan)", source)
        self.assertIn("表示されるのは7", body)

    def test_clone_and_shared_array_are_distinguished(self):
        body = chapter(19)
        for phrase in ("Array.clone", "Array.fork", "@unsafe", "Array.atomic.cas"):
            self.assertIn(phrase, body)

    def test_one_atomic_update_returns_old_value(self):
        body = chapter(19)
        source = text("src/51_atomic_counter.bend")
        self.assertIn("Array.atomic.add(Array.new(U32, 1n, 5), 0, 3)", source)
        self.assertIn("Array.get(U32, array, 0)", source)
        self.assertIn("加算前の値5", body)
        self.assertIn("加算後の値8", body)

    def test_two_cell_fixture_and_scope(self):
        body = chapter(19)
        self.assertEqual((ROOT / "src/56_atomic_two_cells.bend").read_bytes(),
                         (ROOT / "scripts/fixtures/atomic_two_cells.bend").read_bytes())
        self.assertIn("Array.atomic.add(array, 1, 7)", body)
        self.assertIn("順次実行の観測", body)
        self.assertIn("物理GPU", body)

    def test_target42_is_executed_not_only_emitted(self):
        body = chapter(20)
        source = text("src/43_target_hello.bend")
        runner = text("scripts/test_targets.py")
        self.assertIn("(6 * 7 : U32)", source)
        for phrase in ('expected != "42"', 'run(str(native))', 'run("node", str(js))'):
            self.assertIn(phrase, runner)
        self.assertIn("三つで実際に", body)
        self.assertIn("外部FFI", body)

    def test_module_index_needs_caller_bounds(self):
        body = chapter(20)
        self.assertIn("Board.index(3, 2)", text("src/42_module_board.bend"))
        self.assertIn("y * 4 + x", text("src/board_index.bend"))
        self.assertIn("座標を検査していません", body)

    def test_publish_is_not_a_local_exercise(self):
        body = chapter(20)
        self.assertIn("--publish", body)
        self.assertIn("公開操作そのものは行いません", body)
        self.assertIn("モジュールをパッケージとして配るとき", body)
        self.assertIn("パッケージを公開する前に確かめる", body)

    def test_audio_is_typechecked_not_playback_verified(self):
        body = chapter(20)
        source = text("src/26_audio_open.bend")
        self.assertIn("CI checks syntax/types only", source)
        self.assertIn("Audio.open(44100)", source)
        self.assertIn("Audio.close(audio)", source)
        self.assertIn("音は鳴りません", body)
        self.assertIn("実際にスピーカーから音が鳴ったとは判断できません", body)


if __name__ == "__main__":
    unittest.main()
