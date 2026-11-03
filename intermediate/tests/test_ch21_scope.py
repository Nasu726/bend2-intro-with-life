"""Chapter 21 editorial regression and independent 10x10 wall oracle.

These checks do not substitute for Bend execution, X11 acceptance or proof.
"""
from collections import deque
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def chapter(number):
    parts = re.split(r"(?=^\\chapter\{)", source("Intermediate_Textbook.tex"),
                     flags=re.MULTILINE)
    chapters = [part for part in parts if part.startswith(r"\chapter{")]
    return chapters[number - 1]


def neighbors(index, n=10):
    x, y = index % n, index // n
    return [ny * n + nx
            for ny in range(max(0, y - 1), min(n, y + 2))
            for nx in range(max(0, x - 1), min(n, x + 2))
            if (nx, ny) != (x, y)]


def reveal(start, opened, mines):
    """Independent reference flood; numbers at the frontier are opened."""
    queue = deque([start])
    while queue:
        index = queue.popleft()
        if index in opened or index in mines:
            continue
        opened.add(index)
        if not any(adjacent in mines for adjacent in neighbors(index)):
            queue.extend(neighbors(index))


class Chapter21ScopeTest(unittest.TestCase):
    def test_thirteen_sections(self):
        self.assertEqual(len(re.findall(r"^\\section\{", chapter(21), re.M)), 13)

    def test_phase_and_first_click_are_separate(self):
        body = chapter(21)
        self.assertIn("type Phase is Data", body)
        self.assertIn("Start.mine_mask(Start.click(Start.new(1), 0))", body)
        self.assertIn("== 2 : U32", body)
        self.assertIn("def begin_fresh(", source("minesweeper/start.bend"))

    def test_zero_flood_is_bounded(self):
        self.assertIn("explore(129n", source("minesweeper/flood.bend"))
        self.assertIn("def choose_queue(", source("minesweeper/flood.bend"))
        self.assertIn("129", chapter(21))

    def test_cli_has_real_replay_and_expected_display(self):
        self.assertIn("def replay(", source("minesweeper/cli_replay.bend"))
        self.assertIn("c0 f1 c1", chapter(21))
        self.assertIn("2 F . .", chapter(21))

    def test_four_by_four_gui_boundary(self):
        gui = source("minesweeper/gui.bend")
        self.assertIn("def cell_at(", gui)
        self.assertIn("256, 256", gui)
        for coordinate in ("(63,0)", "(64,0)", "(255,255)", "(256,0)"):
            self.assertIn(coordinate, chapter(21))

    def test_cli_save_has_versioned_format(self):
        self.assertIn("BEND2-SAVE-1", source("minesweeper/cli_save.bend"))
        self.assertIn("BEND2-SAVE-1|c0|f1|END", chapter(21))

    def test_ten_by_ten_playthrough_uses_two_clicks(self):
        play = source("minesweeper/nxn_playthrough.bend")
        self.assertIn("Game.click(game, 0)", play)
        self.assertIn("Game.click(game, 99)", play)
        self.assertIn("110", chapter(21))

    def test_independent_wall_flood(self):
        # A wall of ten mines on row five divides 90 safe cells into
        # two zero-connected components with numbered frontiers.
        mines = set(range(50, 60))
        opened = set()
        reveal(0, opened, mines)
        self.assertEqual(len(opened), 50)
        self.assertEqual(opened, set(range(50)))
        reveal(99, opened, mines)
        self.assertEqual(opened, set(range(100)) - mines)

    def test_gui_render_and_environment_boundary(self):
        body = chapter(21)
        self.assertIn("8689825", body)
        self.assertIn("320", body)
        self.assertIn("512", body)
        self.assertIn("X11仮想デスクトップ", body)
        self.assertIn("def view(", source("minesweeper/nxn_gui_render.bend"))

    def test_history_and_input_limits(self):
        self.assertIn("512n", source("minesweeper/nxn_gui_history.bend"))
        self.assertIn("4097", source("minesweeper/nxn_gui_store.bend"))
        self.assertIn("BEND2-GUI-1", chapter(21))

    def test_shipped_status_gui_routes_save_to_atomic_module(self):
        status = source("minesweeper/nxn_gui_status_app.bend")
        self.assertIn("import ./nxn_gui_atomic_store.bend as Atomic", status)
        self.assertIn("Atomic.save_atomic_report(model)", status)
        for marker in ("State{model, 1}", "State{model, 3}",
                       "State{restored, 2}", "State{model, 4}"):
            self.assertIn(marker, status)

    def test_atomic_replacement_is_not_power_loss_durability(self):
        atomic = source("minesweeper/nxn_gui_atomic_store.bend")
        self.assertIn('File.open(temp, "x")', atomic)
        self.assertIn('Process.run("/usr/bin/mv"', atomic)
        self.assertIn("No fsync", atomic)
        body = chapter(21)
        for limit in ("fsync", "スクリーンリーダー", "物理GPU", "他OS"):
            self.assertIn(limit, body)


if __name__ == "__main__":
    unittest.main()
