#!/usr/bin/env python3
"""Finite differential test for Bend's active-session N x N zero cascade.

Independent Python BFS uses coordinate sets, not Bend's packed mine words.
No first-click relocation, victory state, GUI, or general proof is assumed.
"""
from collections import deque
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = (
    "game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
    "nxn_clues.bend", "nxn_step.bend", "nxn_neighbors.bend",
    "nxn_flood.bend",
)


def neighbors(n, index):
    x, y = index % n, index // n
    return tuple(
        v * n + u
        for v in range(max(0, y - 1), min(n, y + 2))
        for u in range(max(0, x - 1), min(n, x + 2))
        if (u, v) != (x, y)
    )


def expected(n, mines, operations, probe):
    mines = set(mines)
    opened, flags = {}, set()
    phase = 0
    for action, index in operations:
        if phase or not 0 <= index < n*n:
            continue
        if action == "mark":
            if index not in opened:
                if index in flags:
                    flags.remove(index)
                else:
                    flags.add(index)
            continue
        if index in opened or index in flags:
            continue
        if index in mines:
            phase = 2
            continue
        pending = deque((index,))
        while pending:
            cell = pending.popleft()
            if cell in opened or cell in flags or cell in mines:
                continue
            nearby = neighbors(n, cell)
            clue = sum(i in mines for i in nearby)
            opened[cell] = clue
            if clue == 0:
                pending.extend(nearby)
    square = (10 + opened[probe] if probe in opened else
              1 if probe in flags else 0 if 0 <= probe < n*n else 99)
    return phase*100 + square


def cases():
    checks = []
    for n in (2, 3, 4):
        last = n*n - 1
        for mines in ((), (last,), (0,), (0, last)):
            for operations, probe in (
                ((("click", 0),), last-1),
                ((("mark", 1), ("click", 0)), 1),
                ((("click", last), ("click", 0)), 0),
            ):
                checks.append((n, mines, operations, probe))
    checks.extend((
        (4, (15,), (("click", 0),), 14),
        (4, (15,), (("click", 0),), 15),
        (4, (15,), (("mark", 1), ("click", 0)), 1),
        (4, (15,), (("mark", 1), ("click", 0), ("mark", 1)), 1),
        (4, (), (("click", 0),), 15),
        (10, (), (("click", 0),), 99),
        (10, (9,), (("click", 10),), 99),
        (10, (9,), (("click", 10),), 9),
        (10, (99,), (("click", 0),), 98),
        (10, (99,), (("click", 100), ("click", 0)), 100),
        (10, (99,), (("mark", 99), ("click", 0)), 99),
        (17, (), (("click", 0),), 288),
        (17, (288,), (("click", 0),), 287),
        (100, (0,), (("click", 1),), 1),
        (100, (9999,), (("click", 9998),), 9998),
        (100, (5000,), (("click", 5001),), 5001),
        (100, (0,), (("click", 10000), ("click", 1)), 10000),
    ))
    return checks


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_step.bend as Step",
        "import ./nxn_flood.bend as Flood", "",
        "def one_if_bool(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0", "",
        "def one_if_equal(+a: U32, +b: U32) -> U32:",
        "  one_if_bool(U32.is_eq(a, b))", "",
    ]
    for k, (n, mines, operations, probe) in enumerate(checks):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  state = Step.new(board)")
        for action, index in operations:
            function = "Step.mark" if action == "mark" else "Flood.click"
            lines.append(f"  state = {function}(state, {index})")
        lines.append(
            f"  one_if_equal(Step.snapshot(state, {probe}), "
            f"{expected(n, mines, operations, probe)})"
        )
        lines.append("")
    for start in range(0, len(checks), 8):
        lines.extend((
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(
                f"case_{i}()" for i in range(start, min(start+8, len(checks)))
            ) + " : U32)", "",
        ))
    lines.extend((
        "def main() -> U32:",
        "  (" + " + ".join(
            f"group_{i}()" for i in range(0, len(checks), 8)
        ) + " : U32)",
    ))
    return "\n".join(lines) + "\n"


def main():
    checks = cases()
    assert len(checks) == 53, len(checks)
    assert expected(4, (15,), (("click", 0),), 14) == 11
    assert expected(10, (9,), (("click", 10),), 99) == 10
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_flood.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N zero flood: {len(checks)} cases / {args[-1]}", flush=True)
            proc = subprocess.run(
                args, cwd=directory, capture_output=True, text=True,
                timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(
                    f"Expected {len(checks)} independent matches; got {proc.stdout}"
                )
    print(f"PASS {len(checks)} independent Bend zero-flood checks")


if __name__ == "__main__":
    main()
