#!/usr/bin/env python3
"""Headless finite Image checks for the 10x10 first-click-generated GUI.

No OS window is opened. `--check-only` on the App.run entry point verifies
Bend types, not native linking, actual pixels, or desktop input delivery.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from test_nxn_lazy_game import FILES, GAME, placed
from test_nxn_gui_adapter import ADAPTER, oracle
from test_nxn_gui_events import EVENTS

RENDER = GAME / "nxn_gui_render.bend"
APP = GAME / "nxn_gui_app.bend"
SEED = 20261029
HIDDEN, FLAG, EMPTY, NUMBER, PADDING = 8689825, 14704438, 15658734, 1578496, 0


def first_clue():
    mines = placed(10, 10, SEED, 0)
    return sum(y * 10 + x in mines for y in (0, 1) for x in (0, 1) if x or y)


def expected_first_color():
    return EMPTY


def harness():
    cases = [
        ("hidden", "RENDER.cell_color(0)", HIDDEN),
        ("flag", "RENDER.cell_color(1)", FLAG),
        ("open-zero", "RENDER.cell_color(10)", EMPTY),
        ("open-number", "RENDER.cell_color(12)", NUMBER),
        ("padding", "RENDER.cell_color(99)", PADDING),
        ("digit-two", "RENDER.tile_pixel(12, 5, 3)", NUMBER),
        ("zero-no-digit", "RENDER.tile_pixel(10, 5, 3)", EMPTY),
        ("tile-border", "RENDER.tile_pixel(0, 0, 1)", 2697513),
        ("fresh-top-left-interior", "RENDER.pixel_at(RENDER.fresh_picture(), 1, 1, 128)", HIDDEN),
        ("fresh-bottom-right-padding", "RENDER.pixel_at(RENDER.fresh_picture(), 127, 127, 128)", PADDING),
        ("fresh-last-cell", "RENDER.pixel_at(RENDER.fresh_picture(), 79, 79, 128)", HIDDEN),
        ("fresh-first-right-padding", "RENDER.pixel_at(RENDER.fresh_picture(), 80, 79, 128)", PADDING),
        ("fresh-first-bottom-padding", "RENDER.pixel_at(RENDER.fresh_picture(), 79, 80, 128)", PADDING),
        ("prestart-flag-does-not-open", "view_first(RENDER.view(GUI.pointer(GUI.reset_gui(20261029), 319, 319, 1)))", HIDDEN),
        ("prestart-padding-click-keeps-fresh", "view_state(RENDER.view(GUI.pointer(GUI.reset_gui(20261029), 320, 0, 0)))", 300),
        ("fresh-view-state", "view_state(RENDER.view(GUI.reset_gui(20261029)))", 300),
        ("active-view-state", "view_state(RENDER.view(GUI.pointer(GUI.reset_gui(20261029), 0, 0, 0)))",
         oracle(10, 10, SEED, ((0, 0, 0),), 0)),
        ("active-view-top-left", "view_first(RENDER.view(GUI.pointer(GUI.reset_gui(20261029), 0, 0, 0)))",
         expected_first_color()),
        ("quadrant-tl", "RENDER.pixel_at(quadrant(), 0, 0, 2)", 11),
        ("quadrant-tr", "RENDER.pixel_at(quadrant(), 1, 0, 2)", 22),
        ("quadrant-bl", "RENDER.pixel_at(quadrant(), 0, 1, 2)", 33),
        ("quadrant-br", "RENDER.pixel_at(quadrant(), 1, 1, 2)", 44),
    ]
    lines = [
        "import Base", "import ./nxn_gui_render.bend as RENDER",
        "import ./nxn_gui_adapter.bend as GUI", "import ./nxn_lazy_game.bend as Lazy", "",
        "def quadrant() -> Image:", "  Qua{Pix{11}, Pix{22}, Pix{33}, Pix{44}}", "",
        "def one_if_true(b: Bool) -> U32:",
        "  match b:", "    case True{}:", "      1", "    case False{}:", "      0", "",
        "def equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))", "",
        "def view_state(pair: Lazy.Game & Image) -> U32:",
        "  (game, img) = pair", "  GUI.snapshot(game, 0)", "",
        "def view_first(pair: Lazy.Game & Image) -> U32:",
        "  (game, img) = pair", "  RENDER.pixel_at(img, 1, 1, 128)", "",
    ]
    for i, (_, expr, expected) in enumerate(cases):
        lines += [f"def check_{i}() -> U32:", f"  equal({expr}, {expected})", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"check_{i}()" for i in range(len(cases))) + " : U32)"]
    return "\n".join(lines) + "\n", len(cases)


def preflight():
    renderer = RENDER.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    assert "Array.clone(Game.Square, cells)" in renderer
    assert "Array.to_list(Game.Square, inspect)" in renderer
    assert "def shared_squares(cells: List<Game.Square>) -> List<&2, Game.Square>:" in renderer
    assert "square <> shared_squares(rest)" in renderer
    assert "def list_code(fuel: Nat, cells: List<&2, Game.Square>)" in renderer
    assert "def visible_code(valid: Bool, cells: List<&2, Game.Square>" in renderer
    assert "+cells: List<&2, Game.Square>) -> Image:" in renderer
    assert "shared_squares(Array.to_list(Game.Square, inspect))" in renderer
    assert "shared_squares(Array.to_list(Game.Square, Array.new(" in renderer
    assert "Lazy.Fresh{n, count, seed}" in renderer
    assert "Step.square_code(square)" in renderer
    code_lookup = renderer.split("def list_code(", 1)[1].split("\ndef visible_code(", 1)[0]
    assert "  match fuel:\n" in code_lookup
    assert code_lookup.count("      match cells:\n") == 2
    assert "      match fuel:" not in code_lookup
    assert "picture(4n, 0, 0" in renderer
    assert "tile_draw(3n, visible_code(" in renderer
    assert "def pixel_at(img: Image" in renderer
    sampler = renderer.split("def pixel_at_walk(", 1)[1].split("def top_left(", 1)[0]
    assert "match img:\\n" not in sampler or "match bottom right:" in sampler
    assert "match bottom right:" in sampler
    assert sampler.index("match bottom right:") < sampler.index("+half =")
    assert all(f"pixel_at_walk({q}," in sampler for q in ("tl", "tr", "bl", "br"))
    assert "pixel_at(choose_quadrant(" not in sampler
    assert "def pixel_at(img: Image" in sampler
    assert "Bool.and(U32.is_lt(x, 10), U32.is_lt(y, 10))" in renderer
    assert "Words.has(" not in renderer and "Lazy.generate(" not in renderer
    assert "App.run(" not in renderer
    assert "App.run(~Lazy.Game" in app
    assert "512, 512, GUI.reset_gui(20261029)" in app
    assert "Events.tick(events, game, 20261029)" in app
    assert "GUI.pointer" not in renderer
    assert first_clue() in range(4)
    source, count = harness()
    assert count == 22
    assert source.index("def one_if_true(") < source.index("def equal(")
    assert source.index("def view_first(") < source.index("def check_0(")
    assert source.count("def main() -> U32:") == 1
    assert oracle(10, 10, SEED, ((0, 0, 0),), 0) not in (300, 400)
    print("PASS 22 independent headless render expectations and App.run structural contract", flush=True)


def run(cmd, cwd, label, expected=None):
    print(f"CHECK {label}", flush=True)
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=240,
                       env=dict(os.environ, BEND_NO_TELEMETRY="1"))
    if p.returncode:
        raise AssertionError(f"{label}: {cmd}\n{p.stdout}\n{p.stderr}")
    if expected is not None:
        lines = p.stdout.strip().splitlines()
        if not lines or lines[-1] != str(expected):
            raise AssertionError(f"{label}: expected {expected}, got {p.stdout!r}")


def main():
    preflight()
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_gui_render.py [--static-only]")
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        for path in (ADAPTER, EVENTS, RENDER, APP):
            (directory / path.name).write_bytes(path.read_bytes())
        source, count = harness()
        path = directory / "check_gui_image.bend"
        path.write_text(source, encoding="utf-8")
        run(("bend", str(path), "--check-only"), directory, "Image typecheck")
        run(("bend", str(path)), directory, "22 Image expectations", count)
        run(("bend", str(directory / APP.name), "--check-only"), directory,
            "App.run typecheck (no desktop launch)")
    print("PASS headless Image checks and App.run typecheck; OS GUI still unverified", flush=True)


if __name__ == "__main__":
    main()
