#!/usr/bin/env python3
"""Finite independent oracle for N x N first-click, flood and terminal transitions.

Bend uses packed words and Array; this oracle uses Python sets and BFS.
N=100 whole-board flood performance, GUI and no-guess solving are not tested.
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
    "nxn_clues.bend", "nxn_step.bend", "nxn_victory.bend",
    "nxn_terminal.bend", "nxn_relocate.bend", "nxn_neighbors.bend",
    "nxn_flood.bend", "nxn_full_game.bend",
)


def neighbors(n, index):
    x, y = index % n, index // n
    return (
        row * n + col
        for row in range(max(0, y - 1), min(n, y + 2))
        for col in range(max(0, x - 1), min(n, x + 2))
        if (col, row) != (x, y)
    )


def expected(n, initial_mines, operations, probe):
    """Independent set/deque model: relocation, flood, win/loss and flags."""
    mines = set(initial_mines)
    opened, flags = {}, set()
    phase = 3
    for action, index in operations:
        if phase == 3:
            if action != "click" or not 0 <= index < n*n or len(mines) == n*n:
                continue
            if index in mines:
                destination = next(i for i in range(n*n) if i not in mines)
                mines.remove(index)
                mines.add(destination)
            phase = 0
        if phase != 0 or not 0 <= index < n*n:
            continue
        if action == "mark":
            if index not in opened:
                if index in flags:
                    flags.remove(index)
                else:
                    flags.add(index)
        elif index not in flags and index not in opened:
            if index in mines:
                phase = 2
            else:
                queue = deque([index])
                while queue:
                    square = queue.popleft()
                    if square in flags or square in opened:
                        continue
                    if square in mines:
                        raise AssertionError("A zero frontier reached a mine")
                    clue = sum(j in mines for j in neighbors(n, square))
                    opened[square] = clue
                    if clue == 0:
                        queue.extend(neighbors(n, square))
                if len(opened) == n*n - len(mines):
                    phase = 1
    if phase == 3:
        return 300
    square = (
        99 if not 0 <= probe < n*n else
        10 + opened[probe] if probe in opened else
        1 if probe in flags else 0
    )
    return 100 * phase + square


def cases():
    checks = []
    traces = (
        (("click", 0),),
        (("click", 0), ("click", 1)),
        (("mark", 0), ("click", 0)),
        (("click", 0), ("mark", 1), ("click", 1)),
    )
    for n in (2, 3, 4):
        last = n*n - 1
        for mines in ((), (0,), (last,), (0, last)):
            for trace in traces:
                checks.append((n, mines, trace, last))
    # Large boards keep a mine next to the click: no full 100x100 flood.
    for n in (10, 17, 100):
        for mines in ((1,), (0,), (0, 1)):
            for trace in (
                (("click", 0),),
                (("click", 0), ("click", 1)),
                (("click", 0), ("mark", 1), ("click", 1)),
                (("click", n*n), ("click", 0)),
            ):
                checks.append((n, mines, trace, 0))
    checks.extend((
        (2, (3,), (("click", 0), ("click", 3)), 0),
        (2, (0, 1, 2), (("click", 0), ("click", 3)), 0),
        (2, tuple(range(4)), (("click", 0),), 0),
        (3, (), (("click", 0), ("mark", 8)), 8),
        (3, (), (("click", 9),), 0),
        (3, (8,), (("click", 0), ("mark", 7), ("click", 7),
                   ("mark", 7), ("click", 7)), 7),
        (10, (1,), (("click", 100),), 0),
        (10, (1,), (("click", 127),), 0),
        (100, (1,), (("click", 10000),), 0),
    ))
    return checks


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_full_game.bend as Game", "",
        "def one_if_true(equal: Bool) -> U32:",
        "  match equal:", "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def one_if_equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))", "",
    ]
    for k, (n, mines, operations, probe) in enumerate(checks):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  game = Game.new(board)")
        for action, index in operations:
            lines.append(f"  game = Game.{action}(game, {index})")
        lines.append(
            f"  one_if_equal(Game.snapshot(game, {probe}), "
            f"{expected(n, mines, operations, probe)})"
        )
        lines.append("")
    for start in range(0, len(checks), 10):
        lines.extend((
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(
                f"case_{i}()" for i in range(start, min(start + 10, len(checks)))
            ) + " : U32)", "",
        ))
    lines.extend((
        "def main() -> U32:",
        "  (" + " + ".join(
            f"group_{i}()" for i in range(0, len(checks), 10)
        ) + " : U32)",
    ))
    return "\n".join(lines) + "\n"


def main():
    checks = cases()
    phases = {expected(n, mines, trace, probe) // 100
              for n, mines, trace, probe in checks}
    assert phases == {0, 1, 2, 3}, phases
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_game.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N full game: {len(checks)} cases / {args[-1]}", flush=True)
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
    print(f"PASS {len(checks)} independent Bend first-click/flood/terminal checks")


if __name__ == "__main__":
    main()
