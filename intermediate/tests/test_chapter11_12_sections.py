"""Section-level static review of Image (11) and App/events (12).

This does not replace Bend runtime checks, X11 GUI acceptance, PDF inspection,
or physical GPU/other-OS tests. Chapter 12 discusses the legacy 4x4 GUI;
the N x N save/restore GUI is a separate chapter-21 implementation.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^\\chapter\{[^}\n]+\}", re.MULTILINE)
SECTION = re.compile(r"^\\section\{([^}\n]+)\}", re.MULTILINE)
SAMPLE = re.compile(r"\\sample\{([^}]+)\}")


def chapter_sections(source: str, number: int) -> list[tuple[str, str]]:
    chapters = list(CHAPTER.finditer(source))
    if len(chapters) != 23:
        raise AssertionError(f"Expected 23 chapters, got {len(chapters)}")
    start = chapters[number - 1].end()
    end = chapters[number].start() if number < len(chapters) else len(source)
    body = source[start:end]
    headings = list(SECTION.finditer(body))
    return [
        (heading.group(1), body[heading.end():
         headings[i + 1].start() if i + 1 < len(headings) else len(body)])
        for i, heading in enumerate(headings)
    ]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class ImageAndEventsReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = read("Intermediate_Textbook.tex")
        cls.chapter11 = chapter_sections(source, 11)
        cls.chapter12 = chapter_sections(source, 12)

    def test_chapter11_four_sections_and_samples(self):
        expected = [
            ("四つのマスを塗り分けてみる", ["31_image_quadrants.bend"]),
            ("Quaの中へさらにQuaを入れる", []),
            ("画像を作る処理と表示する処理を分ける", []),
            ("四分木の深さと画面の大きさを結び付ける", []),
        ]
        self.assertEqual(
            [(title, SAMPLE.findall(body)) for title, body in self.chapter11],
            expected,
        )
        self.assertTrue((ROOT / "src" / "31_image_quadrants.bend").is_file())

    def test_chapter12_eight_sections_and_samples(self):
        expected = [
            ("表示するだけでは画面は変わらない", ["07_gui_hello.bend"]),
            ("viewとtickを一行ずつ読む", []),
            ("マウスから得られるのは盤面の番号ではない", ["23_cell_hit_test.bend"]),
            ("Mouseイベントと座標変換をつなぐ", ["32_mouse_events.bend"]),
            ("マインスイーパーのクリック処理につなぐ", []),
            ("4×4 GUIでは、一マスは64画素になる", []),
            ("クリックからゲーム状態を更新する", []),
            ("viewは盤面を消費せず、画像を組み立てる", []),
        ]
        self.assertEqual(
            [(title, SAMPLE.findall(body)) for title, body in self.chapter12],
            expected,
        )
        for _, samples in expected:
            for sample in samples:
                with self.subTest(sample=sample):
                    self.assertTrue((ROOT / "src" / sample).is_file())

    def test_image_tree_is_pure_and_output_is_observed(self):
        source = read("src/31_image_quadrants.bend")
        self.assertIn("Qua{Pix{16711680}, Pix{0}, Pix{0}, Pix{0}}", source)
        self.assertIn("top_left_color(tl)", source)
        self.assertNotIn("App.run(", source)
        chapter = dict(self.chapter11)
        self.assertIn("結果は\\code{16711680}", chapter["四つのマスを塗り分けてみる"])
        depth = chapter["四分木の深さと画面の大きさを結び付ける"]
        for phrase in ("tile_draw(3n", "8×8画素", "256", "32"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, depth)

    def test_app_tick_and_close_are_not_click_only(self):
        source = read("src/07_gui_hello.bend")
        for phrase in (
            "App.run(~U32", "Con{Close{}, rest}",
            "tick(rest, (color + 1 : U32))",
        ):
            self.assertIn(phrase, source)
        chapter = dict(self.chapter12)
        self.assertIn("マウスをクリックしたときだけ色が変わるプログラムではありません",
                      chapter["viewとtickを一行ずつ読む"])
        self.assertIn("IO(Maybe<U32>)", chapter["viewとtickを一行ずつ読む"])

    def test_8x8_coordinate_example_and_none_boundary(self):
        hit = read("src/23_cell_hit_test.bend")
        mouse = read("src/32_mouse_events.bend")
        for source in (hit, mouse):
            for phrase in ("U32.div(x, 32)", "U32.div(y, 32)",
                           "U32.is_lt(x, 256)", "U32.is_lt(y, 256)"):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, source)
        self.assertIn("Mouse{64, 32, 0, True{}}", mouse)
        self.assertIn("Mouse{256, 0, 0, True{}}", mouse)
        chapter = dict(self.chapter12)
        self.assertIn("結果は\\code{10}",
                      chapter["Mouseイベントと座標変換をつなぐ"])
        self.assertIn("0番のマス",
                      chapter["Mouseイベントと座標変換をつなぐ"])

    def test_4x4_gui_is_distinct_from_8x8_example(self):
        gui = read("minesweeper/gui.bend")
        for phrase in (
            "tile_draw(3n", "Array.clone(Game.Square, cells)",
            "U32.is_lt(x, 256)", "U32.is_lt(y, 256)",
            "U32.is_eq(button, 0)", "U32.is_eq(button, 1)",
            "case Key{27, True{}}:", "case Key{114, True{}}:",
            "case Mouse{x, y, button, True{}}:",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, gui)
        chapter = dict(self.chapter12)
        self.assertIn("64×64画素", chapter["4×4 GUIでは、一マスは64画素になる"])
        self.assertIn("8×8盤面", chapter["マインスイーパーのクリック処理につなぐ"])

    def test_existing_runtime_contract_and_gui_scope(self):
        runner = read("scripts/test_examples.py")
        for phrase in (
            '"31_image_quadrants.bend": "16711680"',
            '"23_cell_hit_test.bend": "10"',
            '"32_mouse_events.bend": "10"',
            'run("bend", str(game / "gui.bend"), "--check-only")',
            'gui_result != "13"',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runner)
        desktop = read("scripts/test_nxn_gui_desktop.py")
        self.assertIn("virtual-display verification", desktop)
        self.assertIn('nxn_gui_app_store.bend', desktop)
        chapter = dict(self.chapter12)
        self.assertIn("実際にウィンドウが開いたことの確認にはなりません",
                      chapter["表示するだけでは画面は変わらない"])
        self.assertIn("実際のゲームは4×4",
                      chapter["マインスイーパーのクリック処理につなぐ"])

    def test_exercises_are_present_without_inventing_gui_results(self):
        for number, sections in ((11, self.chapter11), (12, self.chapter12)):
            body = "\n".join(section for _, section in sections)
            with self.subTest(chapter=number):
                self.assertEqual(body.count(r"\exercise{"), 1)
                self.assertIn("してみましょう", body)


if __name__ == "__main__":
    unittest.main()
