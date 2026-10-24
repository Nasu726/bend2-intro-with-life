#!/usr/bin/env python3
"""Finite Bend/Python pixel-to-cell and pointer-event differential test.

Tests the pure adapter and the real N x N engine. This does NOT validate an
App window, mouse device, rendering, or 100x100 flood performance.
"""
import os
from pathlib import Path
import subprocess
import tempfile

from test_nxn_full_game import FILES, GAME, expected

ROOT = Path(__file__).resolve().parents[1]
POINTER = GAME / "nxn_pointer.bend"
INVALID = 10000


def cell(n, x, y):
    if 2 <= n <= 100 and 0 <= x < n * 32 and 0 <= y < n * 32:
        return (y // 32) * n + x // 32
    return INVALID


def geometry_cases():
    checks = []
    for n in (0, 1, 2, 10, 100, 101, 4294967295):
        points = [(0, 0), (31, 31), (32, 0), (0, 32),
                  (4294967295, 0), (0, 4294967295)]
        if 2 <= n <= 100:
            edge = 32 * n
            points += [(edge - 1, edge - 1), (edge, 0),
                       (0, edge), (edge - 1, 31),
                       (31, edge - 1), (edge - 32, edge - 32)]
        for x, y in points:
            checks.append((n, x, y, cell(n, x, y)))
    return checks


def traces():
    wall = tuple(range(50, 60))
    return [
        (10, wall, ((0, 0, 0),), 49),
        (10, wall, ((0, 0, 0), (319, 319, 1)), 99),
        (10, wall, ((0, 0, 0), (319, 319, 1), (319, 319, 0)), 99),
        (10, wall, ((0, 0, 0), (319, 319, 1), (319, 319, 1),
                    (319, 319, 0)), 99),
        (10, wall, ((0, 0, 0), (320, 319, 0)), 99),
        (10, wall, ((0, 0, 0), (319, 320, 0)), 99),
        (10, wall, ((4294967295, 0, 0),), 0),
        (10, wall, ((0, 0, 2),), 0),
        (10, wall, ((0, 0, 1),), 0),
        (10, wall, ((0, 160, 0),), 50),
        (10, wall, ((0, 0, 0), (0, 160, 0), (319, 319, 0)), 99),
        (10, wall, ((0, 0, 0), (319, 319, 0), (0, 160, 0)), 50),
        (2, (), ((63, 63, 0),), 3),
    ]


def oracle_trace(n, mines, events, probe):
    operations = []
    for x, y, button in events:
        i = cell(n, x, y)
        if i != INVALID and button in (0, 1):
            operations.append(("click" if button == 0 else "mark", i))
    return expected(n, mines, tuple(operations), probe)


def bend_source(geometry, events):
    lines = [
        "import Base",
        "import ./nxn_pointer.bend as Pointer",
        "import ./nxn_mine_words.bend as Words",
        "import ./nxn_full_game.bend as Game", "",
        "def yes(value: Bool) -> U32:",
        "  match value:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0", "",
        "def equal(a: U32, b: U32) -> U32:",
        "  yes(U32.is_eq(a, b))", "",
        "def unwrap(m: Maybe<&2, U32>) -> U32:",
        "  match m:",
        "    case Some{i}:",
        "      i",
        "    case None{}:",
        "      10000", "",
    ]
    names = []
    for k, (n, x, y, answer) in enumerate(geometry):
        name = f"geometry_{k}"
        names.append(name)
        lines += [f"def {name}() -> U32:",
                  f"  equal(unwrap(Pointer.cell_at({n}, {x}, {y})), {answer})", ""]
    for k, (n, mines, actions, probe) in enumerate(events):
        name = f"trace_{k}"
        names.append(name)
        lines += [f"def {name}() -> U32:", f"  board = Words.new({n})"]
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  game = Game.new(board)")
        for x, y, button in actions:
            lines.append(f"  game = Pointer.pointer(game, {n}, {x}, {y}, {button})")
        lines += [f"  equal(Game.snapshot(game, {probe}), "
                  f"{oracle_trace(n, mines, actions, probe)})", ""]
    groups = []
    for start in range(0, len(names), 8):
        group = f"group_{start}"
        groups.append(group)
        lines += [f"def {group}() -> U32:",
                  "  (" + " + ".join(f"{name}()" for name in names[start:start + 8])
                  + " : U32)", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"{name}()" for name in groups) + " : U32)", ""]
    return "\n".join(lines)


def main():
    geometry, events = geometry_cases(), traces()
    assert cell(10, 319, 319) == 99
    assert cell(10, 320, 319) == INVALID
    assert cell(100, 3199, 3199) == 9999
    # These expected values are computed without calling the Bend adapter.
    assert oracle_trace(10, tuple(range(50, 60)), ((0, 0, 0),), 49) == 12
    assert oracle_trace(10, tuple(range(50, 60)),
                        ((0, 0, 0), (319, 319, 0)), 99) == 110
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)
        for name in FILES:
            (folder / name).write_bytes((GAME / name).read_bytes())
        (folder / "nxn_pointer.bend").write_bytes(POINTER.read_bytes())
        program = folder / "check_pointer.bend"
        program.write_text(bend_source(geometry, events), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            run = subprocess.run(args, cwd=folder, capture_output=True,
                                 text=True, timeout=360,
                                 env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if run.returncode:
                raise AssertionError(f"{args}: {run.stdout}\n{run.stderr}")
            if len(args) == 2 and run.stdout.strip().splitlines()[-1] != str(len(geometry) + len(events)):
                raise AssertionError(f"Pointer differential mismatch: {run.stdout}")
    print(f"PASS {len(geometry)} pixel positions and {len(events)} Bend engine traces")


if __name__ == "__main__":
    main()
