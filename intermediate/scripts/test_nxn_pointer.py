#!/usr/bin/env python3
"""Finite Bend/Python differential test of 64px N x N mouse routing.

The independent oracle uses Python integer pixel division, sets and BFS.
This does not open an App window or certify GUI rendering/real mouse events.
"""
import os
from pathlib import Path
import subprocess
import tempfile

from test_nxn_full_game import expected, FILES, GAME

ROOT = Path(__file__).resolve().parents[1]
POINTER = GAME / "nxn_pointer.bend"


def pixel_index(n, x, y):
    col, row = x // 64, y // 64
    if 2 <= n <= 100 and col < n and row < n:
        return row * n + col
    return 10000  # sentinel outside the largest supported 100x100 board


def expected_pointer(n, mines, actions, probe):
    operations = []
    for x, y, button in actions:
        index = pixel_index(n, x, y)
        if index == 10000:
            continue
        if button == 0:
            operations.append(("click", index))
        elif button == 1:
            operations.append(("mark", index))
    return expected(n, mines, tuple(operations), probe)


def cases():
    wall = tuple(range(50, 60))
    return (
        (10, wall, ((0, 0, 0),), 49),
        (10, wall, ((63, 63, 0),), 99),
        (10, wall, ((0, 0, 0), (639, 639, 0)), 99),
        (10, wall, ((639, 639, 0), (0, 0, 0)), 0),
        (10, wall, ((0, 0, 0), (639, 639, 1), (639, 639, 0)), 99),
        (10, wall, ((0, 0, 0), (639, 639, 1),
                    (639, 639, 0), (639, 639, 1), (639, 639, 0)), 99),
        (10, wall, ((0, 0, 0), (0, 320, 0), (639, 639, 0)), 99),
        (10, wall, ((0, 0, 0), (639, 639, 0), (0, 320, 0)), 50),
        (10, wall, ((640, 0, 0),), 0),
        (10, wall, ((0, 640, 0),), 0),
        (10, wall, ((0, 0, 2),), 0),
        (10, wall, ((0, 0, 1),), 0),
        (10, wall, ((0, 0, 0), (640, 0, 0)), 0),
        (10, wall, ((0, 0, 0), (0, 640, 1)), 0),
        (10, wall, ((0, 0, 0), (0, 0, 3)), 0),
        (10, (1,), ((64, 0, 0),), 1),
        (10, (1,), ((0, 0, 0),), 0),
        (10, (1,), ((64, 0, 1), (0, 0, 0)), 0),
        (2, (), ((0, 0, 0),), 3),
        (2, (0, 1, 2, 3), ((0, 0, 0),), 0),
        (3, (4,), ((0, 0, 0),), 0),
        (3, (4,), ((192, 0, 0),), 0),
        (17, (1,), ((0, 0, 0),), 0),
        (17, (1,), ((1088, 0, 0),), 0),
        (100, (1,), ((0, 0, 0),), 0),
        (100, (1,), ((6400, 0, 0),), 0),
        (100, (1,), ((0, 6400, 0),), 0),
        (100, (1,), ((4294967295, 0, 0),), 0),
    )


def geometry_cases():
    return (
        (1, 0, 0), (2, 0, 0), (2, 63, 63), (2, 64, 0),
        (2, 127, 127), (2, 128, 0), (3, 191, 191),
        (10, 63, 64), (10, 64, 63), (10, 639, 639),
        (10, 640, 0), (10, 0, 640), (17, 1087, 1087),
        (17, 1088, 0), (100, 6399, 6399), (100, 6400, 0),
        (100, 0, 6400), (100, 4294967295, 0), (101, 0, 0),
    )


def source(game_checks, cell_checks):
    lines = [
        "import Base",
        "import ./nxn_mine_words.bend as Words",
        "import ./nxn_pointer.bend as Pointer",
        "",
        "def as_u32(result: Maybe<&2, U32>) -> U32:",
        "  match result:",
        "    case None{}:",
        "      10000",
        "    case Some{i}:",
        "      i",
        "",
        "def one_if_true(value: Bool) -> U32:",
        "  match value:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0",
        "",
    ]
    for k, (n, x, y) in enumerate(cell_checks):
        lines.extend((
            f"def cell_{k}() -> U32:",
            f"  one_if_true(U32.is_eq(as_u32(Pointer.cell_at({n}, {x}, {y})), {pixel_index(n, x, y)}))",
            "",
        ))
    for k, (n, mines, actions, probe) in enumerate(game_checks):
        lines.extend((f"def game_{k}() -> U32:", f"  board = Words.new({n})"))
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  state = Pointer.new(board)")
        for x, y, button in actions:
            lines.append(f"  state = Pointer.pointer(state, {x}, {y}, {button})")
        lines.extend((
            f"  one_if_true(U32.is_eq(Pointer.snapshot(state, {probe}), {expected_pointer(n, mines, actions, probe)}))",
            "",
        ))
    calls = [f"cell_{k}()" for k in range(len(cell_checks))]
    calls += [f"game_{k}()" for k in range(len(game_checks))]
    for start in range(0, len(calls), 10):
        lines.extend((
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(calls[start:start + 10]) + " : U32)",
            "",
        ))
    lines.extend((
        "def main() -> U32:",
        "  (" + " + ".join(f"group_{start}()" for start in range(0, len(calls), 10)) + " : U32)",
    ))
    return "\n".join(lines) + "\n"


def main():
    game_checks, cell_checks = cases(), geometry_cases()
    wall = tuple(range(50, 60))
    assert expected_pointer(10, wall, ((0, 0, 0),), 49) == 12
    assert expected_pointer(10, wall, ((0, 0, 0), (639, 639, 0)), 99) == 110
    assert expected_pointer(10, wall, ((640, 0, 0),), 0) == 300
    assert expected_pointer(10, wall, ((0, 0, 2),), 0) == 300
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in (*FILES, POINTER.name):
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_pointer.bend"
        program.write_text(source(game_checks, cell_checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            result = subprocess.run(
                args, cwd=directory, capture_output=True, text=True,
                timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if result.returncode:
                raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
            total = len(game_checks) + len(cell_checks)
            if len(args) == 2 and result.stdout.strip().splitlines()[-1] != str(total):
                raise AssertionError(f"Expected {total} Bend/Python matches: {result.stdout}")
    print(f"PASS {len(cell_checks)} pixel mappings and {len(game_checks)} N x N pointer traces")


if __name__ == "__main__":
    main()
