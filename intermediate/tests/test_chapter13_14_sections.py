"""Static chapter 13/14 review plus independent coordinate oracles.

This does not assert new Bend execution, GUI acceptance, or PDF verification.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^\\chapter\{[^}\n]+\}", re.MULTILINE)
SECTION = re.compile(r"^\\section\{([^}\n]+)\}", re.MULTILINE)
SAMPLE = re.compile(r"\\sample\{([^}]+)\}")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def sections(number: int) -> list[tuple[str, str]]:
    text = read("Intermediate_Textbook.tex")
    chapters = list(CHAPTER.finditer(text))
    assert len(chapters) == 23, len(chapters)
    start = chapters[number - 1].end()
    end = chapters[number].start() if number < len(chapters) else len(text)
    body = text[start:end]
    headings = list(SECTION.finditer(body))
    return [(m.group(1), body[m.end():headings[i + 1].start()
                              if i + 1 < len(headings) else len(body)])
            for i, m in enumerate(headings)]


def pixel_cell(x: int, y: int, width: int, side: int) -> int | None:
    if not (0 <= x < width * side and 0 <= y < width * side):
        return None
    return (y // side) * width + (x // side)


def adjacent(x: int, y: int, mine_x: int, mine_y: int, width: int = 4) -> int:
    return sum(1 for v in range(width) for u in range(width)
               if (u, v) == (mine_x, mine_y)
               and max(abs(u - x), abs(v - y)) == 1)


class Chapter13And14ReviewTest(unittest.TestCase):
    def test_13_four_sections_and_real_samples(self):
        expected = [
            ("まず一つのマスを考える", ["09_minesweeper_status.bend"]),
            ("閉じたマスの地雷は見えない", []),
            ("左上のマスに隣は何個ある？", ["10_board_neighbors.bend"]),
            ("座標を使い、内部では一次元配列に格納する", []),
        ]
        self.assertEqual([(h, SAMPLE.findall(b)) for h, b in sections(13)], expected)
        for _, names in expected:
            for name in names:
                self.assertTrue((ROOT / "src" / name).is_file(), name)

    def test_14_four_sections_and_real_sample(self):
        expected = [
            ("画面の数字と盤面の数字は違う", []),
            ("関数の戻り値と実行結果を確かめる", []),
            ("端をまたぐ値はどうなるか", []),
            ("実際の盤面へ渡す前に", []),
        ]
        self.assertEqual([(h, SAMPLE.findall(b)) for h, b in sections(14)], expected)
        self.assertTrue((ROOT / "src/23_cell_hit_test.bend").is_file())

    def test_flag_example_is_visible_state_only(self):
        code = read("src/09_minesweeper_status.bend")
        for fragment in ("type Square is Data:", "Hidden{}", "Flag{}",
                         "Revealed{nearby: U32}", "is_flag(flip_flag(Hidden{}))"):
            self.assertIn(fragment, code)
        self.assertNotIn("mines:", code)
        chapter = dict(sections(13))
        self.assertIn(r"結果は\code{1}", chapter["まず一つのマスを考える"])
        self.assertIn("最初から地雷の位置を渡すことはできません",
                      chapter["閉じたマスの地雷は見えない"])

    def test_set_neighbor_example_is_non_wrapping(self):
        code = read("src/10_board_neighbors.bend")
        for fragment in ("Set.has(mines", "U32.is_lt(left, 4)",
                         "U32.is_lt(up, 4)", 'Set.add(Set.new(), "1,1")',
                         "adjacent(mines, 0, 0)", "adjacent(mines, 2, 2)"):
            self.assertIn(fragment, code)
        chapter = dict(sections(13))["左上のマスに隣は何個ある？"]
        self.assertIn(r"結果は\code{2}", chapter)
        self.assertIn("二つの位置からそれぞれ数えた結果を足した値", chapter)

    def test_board_index_array_depth_and_checked_access(self):
        board = read("minesweeper/board.bend")
        board4 = read("minesweeper/board4.bend")
        self.assertIn("(y * 4 + x : U32)", board)
        self.assertIn("Array.new(Game.Square, 4n, Game.Hidden{})", board4)
        self.assertIn("U32.is_lt(index, 16)", board4)
        self.assertIn("toggle_if_valid", board4)
        self.assertIn("reveal_if_valid", board4)
        chapter = dict(sections(13))["座標を使い、内部では一次元配列に格納する"]
        self.assertIn(r"長さは\(2^4=16\)", chapter)
        self.assertIn("Array.get", chapter)

    def test_8x8_pixel_bounds_and_six_table_entries(self):
        source = read("src/23_cell_hit_test.bend")
        for fragment in ("(y * 8 + x : U32)", "U32.div(x, 32)",
                         "U32.div(y, 32)", "U32.is_lt(x, 256)",
                         "U32.is_lt(y, 256)"):
            self.assertIn(fragment, source)
        chapter = dict(sections(14))
        table = chapter["端をまたぐ値はどうなるか"]
        cases = [((0, 0), 0), ((31, 31), 0), ((32, 0), 1),
                 ((255, 255), 63), ((256, 0), None), ((0, 256), None)]
        for (x, y), result in cases:
            with self.subTest(x=x, y=y):
                self.assertEqual(pixel_cell(x, y, 8, 32), result)
                expected = f"\\code{{Some{{{result}}}}}" if result is not None else r"\code{None{}}"
                self.assertIn(f"({x},{y}) & {expected}", table)
        self.assertIn("六つの境界例をすべて実行した結果ではありません",
                      chapter["関数の戻り値と実行結果を確かめる"])

    def test_none_is_not_click_on_cell_zero(self):
        chapter = dict(sections(14))
        self.assertIn("0番マスの操作と誤認",
                      chapter["関数の戻り値と実行結果を確かめる"])
        self.assertEqual(pixel_cell(256, 0, 8, 32), None)
        self.assertEqual(pixel_cell(0, 0, 8, 32), 0)

    def test_existing_bend_runtime_is_not_six_case_execution(self):
        runner = read("scripts/test_examples.py")
        for fragment in ('"09_minesweeper_status.bend": "1"',
                         '"10_board_neighbors.bend": "2"',
                         '"23_cell_hit_test.bend": "10"',
                         'gui_result != "13"'):
            self.assertIn(fragment, runner)
        gui_smoke = read("minesweeper/gui_smoke.bend")
        self.assertIn("The GUI window is not opened", gui_smoke)
        self.assertIn("Gui.cell_at(255, 255)", gui_smoke)
        self.assertIn("Gui.cell_at(256, 20)", gui_smoke)

    def test_exercises_preserve_predict_execute_compare_flow(self):
        for number in (13, 14):
            chapter = "\n".join(b for _, b in sections(number))
            self.assertEqual(chapter.count(r"\exercise{"), 1)
            if number == 13:
                self.assertIn("予想", chapter)
            else:
                self.assertIn("期待値", chapter)
            self.assertIn("実行", chapter)
            self.assertIn("みましょう", chapter)

    def test_reference_neighbors_for_corner_and_center(self):
        for mine in ((1, 1), (0, 0), (3, 3)):
            with self.subTest(mine=mine):
                total = sum(adjacent(x, y, *mine) for y in range(4) for x in range(4))
                expected = 8 if mine == (1, 1) else 3
                self.assertEqual(total, expected)
        self.assertEqual(adjacent(0, 0, 1, 1), 1)
        self.assertEqual(adjacent(2, 2, 1, 1), 1)
        self.assertEqual(adjacent(3, 3, 0, 0), 0)

    def test_4x4_and_8x8_are_distinct(self):
        self.assertEqual(pixel_cell(64, 32, 8, 32), 10)
        self.assertEqual(pixel_cell(64, 32, 4, 64), 1)
        self.assertEqual(pixel_cell(255, 255, 4, 64), 15)
        self.assertIsNone(pixel_cell(256, 0, 4, 64))


if __name__ == "__main__":
    unittest.main()
