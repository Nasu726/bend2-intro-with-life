#!/usr/bin/env python3
"""Independent finite oracle for the N x N Fresh -> Active first click.

Only single-cell opening is expected: zero flood and victory are not implemented.
The reference uses Python sets and coordinates, not Bend's U32 word layout.
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
    "nxn_clues.bend", "nxn_step.bend", "nxn_relocate.bend", "nxn_start.bend",
)


def expected(n, initial_mines, operations, probe):
    mines = set(initial_mines)
    opened, flags = {}, set()
    fresh, lost = True, False
    for action, index in operations:
        if fresh:
            if action != "click" or not 0 <= index < n * n:
                continue
            if len(mines) == n * n:
                continue
            if index in mines:
                destination = next(i for i in range(n * n) if i not in mines)
                mines.remove(index)
                mines.add(destination)
            fresh = False
        if lost or not 0 <= index < n * n:
            continue
        if action == "mark":
            if index not in opened:
                if index in flags:
                    flags.remove(index)
                else:
                    flags.add(index)
        elif index not in flags and index not in opened:
            if index in mines:
                lost = True
            else:
                x, y = index % n, index // n
                opened[index] = sum(
                    j in mines for j in range(n * n)
                    if j != index and abs(j % n - x) <= 1
                    and abs(j // n - y) <= 1
                )
    if fresh:
        return 300
    visible = (
        99 if not 0 <= probe < n * n else
        10 + opened[probe] if probe in opened else
        1 if probe in flags else 0
    )
    return (200 if lost else 0) + visible


def cases():
    rng = random.Random(20261024)
    result = []
    for n in (2, 3, 4, 10, 17, 100):
        last = n * n - 1
        mine_sets = ((), (0,), (1,), (last,), (0, last))
        actions = (
            ([("click", 0)], 0),
            ([("click", 0), ("click", 1)], 0),
            ([("click", n * n), ("click", 0)], 0),
            ([("mark", 0), ("click", 0)], 0),
            ([("click", 0), ("mark", last), ("click", last)], last),
            ([("click", last)], last),
        )
        for mines in mine_sets:
            for operations, probe in actions:
                result.append((n, mines, operations, probe))
        # Invalid logical indices must not start a game or alias padding.
        padding = 1 << (n * n - 1).bit_length()
        if padding > n * n:
            result.append((n, (0,), [("click", padding - 1)], 0))
        if n < 100:
            for _ in range(3):
                mines = tuple(sorted(rng.sample(range(n * n), min(3, n * n - 1))))
                operations = [
                    (rng.choice(("mark", "click")), rng.randrange(n * n + 2))
                    for _ in range(3)
                ]
                result.append((n, mines, operations, rng.randrange(n * n)))
    # No destination exists: rejected first click remains Fresh.
    for n in (2, 3):
        result.append((n, tuple(range(n * n)), [("click", 0)], 0))
        result.append((n, tuple(range(n * n)), [("click", n * n - 1)], 0))
    # Explicit post-relocation mine hit: mine 0 moves to 1.
    result.append((10, (0,), [("click", 0), ("click", 1)], 0))
    result.append((10, (0,), [("click", 0), ("click", 1), ("mark", 2)], 2))
    return result


def source(all_cases):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_start.bend as Start", "",
        "def one_if_true(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0", "",
        "def one_if_equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))", "",
    ]
    for k, (n, mines, operations, probe) in enumerate(all_cases):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  stage = Start.new(board)")
        for action, index in operations:
            lines.append(f"  stage = Start.{action}(stage, {index})")
        lines.append(
            f"  one_if_equal(Start.snapshot(stage, {probe}), "
            f"{expected(n, mines, operations, probe)})"
        )
        lines.append("")
    lines.append("def main() -> U32:")
    lines.append(
        "  (" + " + ".join(f"case_{i}()" for i in range(len(all_cases))) +
        " : U32)"
    )
    return "\n".join(lines) + "\n"


def main():
    all_cases = cases()
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        path = directory / "check_nxn_start.bend"
        path.write_text(source(all_cases), encoding="utf-8")
        for args in (("bend", str(path), "--check-only"), ("bend", str(path))):
            print(f"CHECK N x N Fresh/Active: {len(all_cases)} cases / {args[-1]}", flush=True)
            proc = subprocess.run(
                args, cwd=directory, capture_output=True, text=True,
                timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(all_cases)):
                raise AssertionError(
                    f"Expected {len(all_cases)} independent matches; got {proc.stdout}"
                )
    print(f"PASS {len(all_cases)} independent Bend first-click session checks")


if __name__ == "__main__":
    main()
