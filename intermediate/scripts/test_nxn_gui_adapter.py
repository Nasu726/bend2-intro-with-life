#!/usr/bin/env python3
"""Independent pixel routing oracle for N x N lazy Minesweeper.

Finite tests of a pure event controller; not GUI rendering or desktop E2E.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from test_nxn_lazy_game import FILES, GAME, expected

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = GAME / "nxn_gui_adapter.bend"
INVALID = 65535

GEOMETRY = (
    (2, 0, 0), (2, 31, 31), (2, 32, 0), (2, 63, 63),
    (2, 64, 0), (2, 0, 64), (2, 63, 64),
    (10, 0, 0), (10, 31, 31), (10, 32, 0),
    (10, 319, 319), (10, 320, 0), (10, 0, 320),
    (10, 319, 0), (10, 0, 319), (10, 95, 63),
    (100, 3199, 3199), (100, 3200, 0),
)

# (n, mine count, seed, pixel operations (x,y,button), inspected cell)
TRACES = (
    (2, 1, 0, (), 0),
    (2, 1, 0, ((64, 0, 0),), 0),
    (2, 1, 0, ((0, 64, 0),), 0),
    (2, 1, 0, ((0, 0, 1),), 0),
    (2, 1, 0, ((0, 0, 2),), 0),
    (2, 0, 0, ((0, 0, 0),), 0),
    (2, 1, 20261028, ((32, 0, 0),), 1),
    (2, 1, 20261028, ((0, 0, 1), (32, 0, 0)), 1),
    (2, 1, 20261028, ((64, 0, 0), (32, 0, 0)), 1),
    (2, 1, 20261028, ((32, 0, 0), (0, 0, 1)), 0),
    (2, 1, 20261028, ((32, 0, 0), (0, 0, 0)), 0),
    (3, 2, 2, ((95, 95, 0),), 8),
    (10, 10, 0, ((320, 0, 0), (0, 0, 1)), 0),
)


def index(n, x, y):
    if not (0 <= x < n * 32 and 0 <= y < n * 32):
        return INVALID
    return (y // 32) * n + (x // 32)


def oracle(n, count, seed, operations, probe):
    game_ops = []
    for x, y, button in operations:
        cell = index(n, x, y)
        if cell != INVALID and button in (0, 1):
            game_ops.append(("click" if button == 0 else "mark", cell))
    return expected(n, count, seed, tuple(game_ops), probe)


def preflight():
    assert len(GEOMETRY) == 18 and len(TRACES) == 13
    assert ADAPTER.is_file()
    source = ADAPTER.read_text(encoding="utf-8")
    assert "import ./nxn_lazy_game.bend as Lazy" in source
    assert "Lazy.click(game, index)" in source
    assert "Lazy.mark(game, index)" in source
    assert "  App.run(" not in source
    assert "def reset_gui(seed: U32)" in source
    assert "def pointer(game: Lazy.Game" in source
    assert index(2, 31, 31) == 0
    assert index(2, 32, 0) == 1
    assert index(2, 63, 63) == 3
    assert index(10, 319, 319) == 99
    assert index(10, 320, 0) == INVALID
    assert index(100, 3199, 3199) == 9999
    assert all(0 <= n <= 100 for n, _, _ in GEOMETRY)
    assert all(oracle(*t) in range(0, 401) for t in TRACES)
    assert all(oracle(*t) == 300 for t in TRACES[:5])
    assert oracle(*TRACES[7]) == oracle(*TRACES[6])
    assert oracle(*TRACES[8]) == oracle(*TRACES[6])
    print("PASS independent pixel geometry and 13 game reference traces", flush=True)


def harness(geometry, traces):
    lines = [
        "import Base", "import ./nxn_gui_adapter.bend as GUI", "",
        "def equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))", "",
        "def one_if_true(b: Bool) -> U32:",
        "  match b:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
    ]
    cases = []
    for k, (n, x, y) in enumerate(geometry):
        lines.extend([f"def geom_{k}() -> U32:",
                      f"  equal(GUI.pixel_index({n}, {x}, {y}), {index(n,x,y)})", ""])
        cases.append(f"geom_{k}()")
    for k, (n, count, seed, ops, probe) in enumerate(traces):
        lines += [f"def trace_{k}() -> U32:",
                  f"  g = GUI.reset({n}, {count}, {seed})"]
        for x, y, button in ops:
            lines.append(f"  g = GUI.pointer_n(g, {n}, {x}, {y}, {button})")
        lines.extend([f"  equal(GUI.snapshot(g, {probe}), "
                      f"{oracle(n,count,seed,ops,probe)})", ""])
        cases.append(f"trace_{k}()")
    # Exercise the fixed 10x10 GUI-facing wrappers without allocating a board.
    if geometry:
        lines += [
            "def gui_reset_flag() -> U32:",
            "  equal(GUI.snapshot(GUI.pointer(GUI.reset_gui(20261029), 319, 319, 1), 99), 300)", "",
            "def gui_reset_outside() -> U32:",
            "  equal(GUI.snapshot(GUI.pointer(GUI.reset_gui(20261029), 320, 0, 0), 0), 300)", "",
            "def gui_reset_middle() -> U32:",
            "  equal(GUI.snapshot(GUI.pointer(GUI.reset_gui(20261029), 0, 0, 2), 0), 300)", "",
        ]
        cases.extend(("gui_reset_flag()", "gui_reset_outside()", "gui_reset_middle()"))
    lines.extend(["def main() -> U32:",
                  "  (" + " + ".join(cases) + " : U32)"])
    return "\n".join(lines) + "\n"


def run_bend(source, directory, expected_count, label):
    for cmd in (("bend", str(source), "--check-only"), ("bend", str(source))):
        print(f"CHECK {label}: {'typecheck' if len(cmd) == 3 else 'run'}",
              flush=True)
        p = subprocess.run(cmd, cwd=directory, text=True, capture_output=True,
                           timeout=180,
                           env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if p.returncode:
            raise AssertionError(f"{label}: {cmd}\n{p.stdout}\n{p.stderr}")
        if len(cmd) == 2:
            output = p.stdout.strip().splitlines()
            if not output or output[-1] != str(expected_count):
                raise AssertionError(
                    f"{label}: expected {expected_count}, got {output}")


def main():
    preflight()
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_gui_adapter.py [--static-only]")
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        (directory / ADAPTER.name).write_bytes(ADAPTER.read_bytes())
        geom = directory / "check_gui_geometry.bend"
        geom.write_text(harness(GEOMETRY, ()), encoding="utf-8")
        run_bend(geom, directory, len(GEOMETRY) + 3, "18 pixel coordinates and 3 GUI wrapper cases")
        for start in range(0, len(TRACES), 3):
            traces = TRACES[start:start + 3]
            target = directory / f"check_gui_game_{start}.bend"
            target.write_text(harness((), traces), encoding="utf-8")
            run_bend(target, directory, len(traces),
                     f"game traces {start+1}-{start+len(traces)}/{len(TRACES)}")
    print("PASS 18 Bend pixel coordinates, 3 fixed-GUI wrappers and 13 Bend game traces", flush=True)


if __name__ == "__main__":
    main()
