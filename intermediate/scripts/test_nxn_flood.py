#!/usr/bin/env python3
"""Independent finite BFS oracle for active N x N zero cascade.

Checks flags, non-wrapping neighbors, mine loss, previously Open squares,
logical padding and several board sizes. Not a universal proof; not a
first-click or victory/GUI test.
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
    "nxn_clues.bend", "nxn_neighbors.bend", "nxn_step.bend",
    "nxn_flood.bend",
)


def neighbors(n, index):
    x, y = index % n, index // n
    return (
        v * n + u
        for v in range(max(0, y - 1), min(n, y + 2))
        for u in range(max(0, x - 1), min(n, x + 2))
        if (u, v) != (x, y)
    )


def clue(n, mines, index):
    return sum(j in mines for j in neighbors(n, index))


def expected(n, initial_mines, flags, preopened, clicked, probe):
    mines = set(initial_mines)
    opened = {i: clue(n, mines, i) for i in preopened}
    marked = set(flags) - set(preopened)
    phase = 0
    if 0 <= clicked < n * n and clicked not in marked and clicked not in opened:
        if clicked in mines:
            phase = 2
        else:
            work = deque([clicked])
            while work:
                index = work.popleft()
                if index in marked or index in opened or index in mines:
                    continue
                number = clue(n, mines, index)
                opened[index] = number
                if number == 0:
                    work.extend(neighbors(n, index))
    square = (
        99 if not 0 <= probe < n * n else
        10 + opened[probe] if probe in opened else
        1 if probe in marked else 0
    )
    return 100 * phase + square


def cases():
    checks = []
    for n in (2, 3, 4, 5):
        last = n * n - 1
        for mines in ((), (0,), (last,), (0, last)):
            for clicked, probe in ((0, 0), (0, last), (last, 0), (last, last)):
                checks.append((n, mines, (), (), clicked, probe))
    checks.extend((
        (3, (), (4,), (), 0, 4),  # Flag must survive an all-zero cascade.
        (3, (), (4,), (), 0, 8),
        (3, (), (), (0,), 0, 8),  # Re-clicking Open zero is a no-op.
        (3, (8,), (1,), (), 0, 1),
        (3, (8,), (1,), (), 0, 4),
        (4, (15,), (), (), 0, 14),
        (4, (0,), (), (), 0, 0),  # Mine loss.
        (10, tuple(range(20, 30)), (), (), 0, 19),
        (10, tuple(range(20, 30)), (), (), 0, 99),
        (10, (1,), (), (), 0, 0),
        (10, (1,), (), (), 100, 0),
        (10, (1,), (), (), 127, 0),
        (17, (1,), (), (), 0, 0),
        (100, (1,), (), (), 0, 0),
        (100, (0,), (), (), 0, 0),
        (100, (1,), (), (), 10000, 0),
    ))
    return checks


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_step.bend as Step",
        "import ./nxn_flood.bend as Flood", "",
        "def one_if_true(b: Bool) -> U32:",
        "  match b:", "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))", "",
    ]
    for k, (n, mines, flags, preopened, clicked, probe) in enumerate(checks):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for index in mines:
            lines.append(f"  board = Words.set_checked(board, {index}, True{{}})")
        lines.append("  session = Step.new(board)")
        for index in preopened:
            lines.append(f"  session = Step.click(session, {index})")
        for index in flags:
            lines.append(f"  session = Step.mark(session, {index})")
        lines.append(f"  session = Flood.reveal(session, {clicked})")
        lines.append(
            f"  equal(Step.snapshot(session, {probe}), "
            f"{expected(n, mines, flags, preopened, clicked, probe)})"
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
    assert any(expected(*case) == 10 for case in checks)
    assert any(expected(*case) >= 200 for case in checks)
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
                    f"Expected {len(checks)} BFS matches; got {proc.stdout}"
                )
    print(f"PASS {len(checks)} independent N x N zero-cascade checks")


if __name__ == "__main__":
    main()
