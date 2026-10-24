#!/usr/bin/env python3
"""Finite differential test for N x N zero flood on an active Bend session.

The independent Python oracle uses sets and coordinate neighbors. It checks
actual opened clues, flags, loss, boundary/padding rejection and the existing
victory predicate. No general proof, first-click relocation or GUI is claimed.
"""
from collections import deque
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = (
    "game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
    "nxn_clues.bend", "nxn_neighbors.bend", "nxn_step.bend",
    "nxn_flood.bend", "nxn_victory.bend",
)


def neighbors(n, index):
    x, y = index % n, index // n
    return [
        j for j in range(n * n)
        if j != index and abs(j % n - x) <= 1
        and abs(j // n - y) <= 1
    ]


def reference(n, mines, operations):
    mines = set(mines)
    opened, flags = {}, set()
    lost = False
    for action, index in operations:
        if lost or not 0 <= index < n * n:
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
        queue = deque([index])
        while queue and not lost:
            current = queue.popleft()
            if current in opened or current in flags:
                continue
            if current in mines:
                lost = True
                break
            clue = sum(j in mines for j in neighbors(n, current))
            opened[current] = clue
            if clue == 0:
                queue.extend(neighbors(n, current))
    won = not lost and len(mines) < n * n and all(
        i in opened for i in range(n * n) if i not in mines
    )
    return opened, flags, lost, won


def expected(n, mines, operations, probe):
    opened, flags, lost, won = reference(n, mines, operations)
    if probe is None:
        return int(won)
    visible = (
        99 if not 0 <= probe < n * n else
        10 + opened[probe] if probe in opened else
        1 if probe in flags else 0
    )
    return (200 if lost else 0) + visible


def cases():
    # Small, nonredundant finite gate. Full 17x17/100x100 cascades
    # belong to separate performance tests, not this CI smoke.
    return [
        (2, (), (("click", 0),), 3),
        (2, (), (("click", 0),), None),
        (2, (3,), (("click", 0),), 0),
        (2, (3,), (("click", 3),), 3),
        (2, (3,), (("mark", 0), ("click", 0)), 0),
        (2, (3,), (("mark", 0), ("mark", 0), ("click", 0)), 0),
        (3, (), (("click", 0),), 8),
        (3, (8,), (("click", 0),), 7),
        (3, (8,), (("click", 0),), None),
        (3, (0,), (("click", 0),), 0),
        (3, (0,), (("click", 1),), 1),
        (4, (), (("click", 0),), 15),
        (4, (), (("mark", 1), ("click", 0)), 1),
        (4, (), (("mark", 1), ("click", 0)), None),
        (4, (), (("mark", 1), ("click", 0), ("mark", 1), ("click", 1)), None),
        (4, (15,), (("click", 0),), 14),
        (4, (15,), (("click", 0),), None),
        (4, (0, 15), (("click", 1),), 0),
        (4, (0, 15), (("click", 0),), 0),
        (10, (), (("click", 0),), 99),
        (10, (9,), (("click", 10),), 19),
        (10, (99,), (("click", 0),), 98),
        (10, (0,), (("click", 1),), 1),
        (10, (0,), (("click", 0),), 0),
        (10, (0,), (("click", 100),), 100),
        (17, (0,), (("click", 1),), 1),
        (17, (0,), (("click", 0),), 0),
        (17, (288,), (("click", 287),), 287),
        (100, (0,), (("click", 1),), 1),
        (100, (0,), (("click", 0),), 0),
        (100, (9999,), (("click", 9998),), 9998),
        (100, (0,), (("click", 10000),), 10000),
    ]


def source(checks):
    lines = [
        "import Base",
        "import ./nxn_mine_words.bend as Words",
        "import ./nxn_step.bend as Step",
        "import ./nxn_flood.bend as Flood",
        "import ./nxn_victory.bend as Win", "",
        "def bool_to_u32(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0", "",
        "def eq(a: U32, b: U32) -> U32:",
        "  bool_to_u32(U32.is_eq(a, b))", "",
    ]
    for k, (n, mines, ops, probe) in enumerate(checks):
        lines += [f"def case_{k}() -> U32:", f"  board = Words.new({n})"]
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  session = Step.new(board)")
        for action, index in ops:
            fn = "Flood.click" if action == "click" else "Step.mark"
            lines.append(f"  session = {fn}(session, {index})")
        actual = (
            "Win.verdict(Win.inspect(session))" if probe is None
            else f"Step.snapshot(session, {probe})"
        )
        lines.append(f"  eq({actual}, {expected(n, mines, ops, probe)})")
        lines.append("")
    for start in range(0, len(checks), 8):
        lines.append(f"def group_{start}() -> U32:")
        lines.append("  (" + " + ".join(
            f"case_{i}()" for i in range(start, min(start + 8, len(checks)))
        ) + " : U32)")
        lines.append("")
    lines.append("def main() -> U32:")
    lines.append("  (" + " + ".join(
        f"group_{i}()" for i in range(0, len(checks), 8)
    ) + " : U32)")
    return "\n".join(lines) + "\n"


def main():
    checks = cases()
    assert any(expected(n, mines, ops, p) == 1 for n, mines, ops, p in checks if p is None)
    assert any(expected(n, mines, ops, p) == 0 for n, mines, ops, p in checks if p is None)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_flood.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N flood: {len(checks)} cases / {args[-1]}", flush=True)
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
    print(f"PASS {len(checks)} independent Bend flood checks")


if __name__ == "__main__":
    main()
