#!/usr/bin/env python3
"""Finite independent BFS oracle for N x N Bend zero flood on active boards."""
from collections import deque
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
         "nxn_clues.bend", "nxn_neighbors.bend", "nxn_step.bend",
         "nxn_flood.bend")


def adjacent(n, index):
    x, y = index % n, index // n
    return (
        row * n + col
        for row in range(max(0, y - 1), min(n, y + 2))
        for col in range(max(0, x - 1), min(n, x + 2))
        if (col, row) != (x, y)
    )


def expected(n, mines, flags, click, inspect):
    mines, flags = set(mines), set(flags)
    opened = set()
    lost = False
    if 0 <= click < n * n and click not in flags:
        if click in mines:
            lost = True
        else:
            work = deque((click,))
            while work:
                cell = work.popleft()
                if cell in opened or cell in flags or cell in mines:
                    continue
                opened.add(cell)
                if not any(i in mines for i in adjacent(n, cell)):
                    work.extend(adjacent(n, cell))
    if not 0 <= inspect < n * n:
        visible = 99
    elif inspect in flags:
        visible = 1
    elif inspect in opened:
        visible = 10 + sum(i in mines for i in adjacent(n, inspect))
    else:
        visible = 0
    return (200 if lost else 0) + visible


def cases():
    boards = [
        (2, (), (), 0, (0, 1, 3)),
        (2, (3,), (), 0, (0, 1, 2, 3)),
        (3, (8,), (), 0, (0, 1, 4, 7, 8)),
        (4, (0,), (), 5, (0, 1, 5, 10, 15)),
        (4, (0, 15), (), 5, (0, 1, 5, 10, 15)),
        (4, (15,), (), 0, (0, 5, 14, 15)),
        (4, (15,), (1,), 0, (0, 1, 5, 14)),
        (4, (15,), (0,), 0, (0, 1, 5)),
        (4, (0,), (), 0, (0, 1, 15)),
        (4, (0,), (), 16, (0, 1, 16)),
        (10, (99,), (), 0, (0, 9, 55, 98, 99, 100, 127)),
        (10, (), (), 0, (0, 9, 99, 100, 127)),
        (10, (0,), (), 0, (0, 1, 99)),
        (17, (288,), (), 0, (0, 1, 17, 288)),
        (100, (1,), (), 0, (0, 1, 2, 9999, 10000)),
    ]
    return [(n, mines, flags, click, inspect)
            for n, mines, flags, click, inspected in boards
            for inspect in inspected]


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_step.bend as Step",
        "import ./nxn_flood.bend as Flood", "",
        "def as_u32(ok: Bool) -> U32:",
        "  match ok:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0", "",
        "def same(a: U32, b: U32) -> U32:",
        "  as_u32(U32.is_eq(a, b))", "",
    ]
    for k, (n, mines, flags, click, inspect) in enumerate(checks):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for index in mines:
            lines.append(f"  board = Words.set_checked(board, {index}, True{{}})")
        lines.append("  session = Step.new(board)")
        for index in flags:
            lines.append(f"  session = Step.mark(session, {index})")
        lines.append(
            f"  same(Step.snapshot(Flood.click(session, {click}), {inspect}), "
            f"{expected(n, mines, flags, click, inspect)})"
        )
        lines.append("")
    for first in range(0, len(checks), 10):
        lines.append(f"def group_{first}() -> U32:")
        lines.append("  (" + " + ".join(
            f"case_{i}()" for i in range(first, min(first + 10, len(checks)))
        ) + " : U32)")
        lines.append("")
    lines.append("def main() -> U32:")
    lines.append("  (" + " + ".join(
        f"group_{i}()" for i in range(0, len(checks), 10)
    ) + " : U32)")
    return "\n".join(lines) + "\n"


def main():
    checks = cases()
    assert any(expected(*case) >= 200 for case in checks)
    assert any(expected(*case) == 99 for case in checks)
    assert any(expected(*case) >= 10 for case in checks)
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
    print(f"PASS {len(checks)} independent N x N zero flood checks")


if __name__ == "__main__":
    main()
