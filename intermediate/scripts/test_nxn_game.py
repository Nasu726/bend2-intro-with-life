#!/usr/bin/env python3
"""Finite independent oracle for Fresh -> terminal N x N transitions.

No zero flood: one safe square is revealed per click. The reference model
uses sets and Cartesian coordinates rather than Bend's packed U32 words.
"""
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = (
    "game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
    "nxn_clues.bend", "nxn_step.bend", "nxn_victory.bend",
    "nxn_terminal.bend", "nxn_relocate.bend", "nxn_game.bend",
)


def expected(n, initial_mines, operations, probe):
    mines = set(initial_mines)
    opened, flags = {}, set()
    phase = 3  # Fresh=3, Playing=0, Won=1, Lost=2
    for action, index in operations:
        if phase == 3:
            if action != "click" or not 0 <= index < n * n or len(mines) == n * n:
                continue
            if index in mines:
                destination = next(i for i in range(n * n) if i not in mines)
                mines.remove(index)
                mines.add(destination)
            phase = 0
        if phase != 0 or not 0 <= index < n * n:
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
                x, y = index % n, index // n
                opened[index] = sum(
                    j in mines for j in range(n * n)
                    if j != index and abs(j % n - x) <= 1
                    and abs(j // n - y) <= 1
                )
                if len(opened) == n * n - len(mines):
                    phase = 1
    if phase == 3:
        return 300
    square = (
        99 if not 0 <= probe < n * n else
        10 + opened[probe] if probe in opened else
        1 if probe in flags else 0
    )
    return 100 * phase + square


def cases():
    checks = []
    for n in (2, 3, 4, 10, 17, 100):
        last = n * n - 1
        minesets = ((), (0,), (1,), (last,), (0, last))
        traces = (
            (("mark", 0), ("click", 0)),
            (("click", n * n), ("click", 0)),
            (("click", 0), ("click", 1)),
            (("click", 0), ("mark", last), ("click", last)),
            (("click", last), ("mark", 0)),
        )
        for mines in minesets:
            for trace in traces:
                checks.append((n, mines, trace, trace[-1][1] % (n * n)))
        # Padding cells must never start the game (10x10: 100..127).
        padding = 1 << (n * n - 1).bit_length()
        if padding > n * n:
            checks.append((n, (0,), (("click", padding - 1),), 0))
    # Complete on first click, including a relocated mine and all-but-one mines.
    checks.extend((
        (2, (0, 1, 2), (("click", 0), ("click", 1), ("mark", 3)), 0),
        (2, (1, 2, 3), (("click", 0), ("click", 1)), 0),
        (2, (3,), (("click", 0), ("click", 1), ("click", 2),
                   ("click", 3), ("mark", 0)), 2),
        (2, (3,), (("click", 0), ("mark", 1), ("click", 2),
                   ("click", 1), ("mark", 1), ("click", 1)), 1),
        (3, tuple(range(9)), (("click", 0), ("click", 8)), 0),
        (10, (0,), (("click", 0), ("click", 1), ("mark", 2)), 2),
        (10, (99,), (("click", 100), ("click", 127), ("mark", 0)), 0),
    ))
    rng = random.Random(20261024)
    for n in (3, 4, 10, 17, 100):
        for _ in range(4):
            mines = tuple(sorted(rng.sample(range(n*n), 2)))
            trace = tuple((rng.choice(("click", "mark")), rng.randrange(n*n+2))
                          for _ in range(3))
            checks.append((n, mines, trace, rng.randrange(n*n)))
    return checks


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_game.bend as Game", "",
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
            print(f"CHECK N x N integrated game: {len(checks)} cases / {args[-1]}", flush=True)
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
    print(f"PASS {len(checks)} independent Bend first-click/terminal checks")


if __name__ == "__main__":
    main()
