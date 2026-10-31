#!/usr/bin/env python3
"""Finite independent oracle for the N x N Bend victory *predicate*.

Step itself still has Playing/Lost, not Won; this test does not claim flood
or integrated terminal-state behavior. Python uses sets and coordinates,
not Bend's U32 word layout or Array capacity.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = (
    "game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
    "nxn_clues.bend", "nxn_step.bend", "nxn_victory.bend",
)


def expected(n, mines, operations):
    mines = set(mines)
    opened, flags = set(), set()
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
        elif index not in flags and index not in opened:
            if index in mines:
                lost = True
            else:
                opened.add(index)
    return not lost and len(mines) < n * n and all(
        i in opened for i in range(n * n) if i not in mines
    )


def cases():
    checks = []
    for n in (2, 3, 4, 10, 17, 100):
        last = n * n - 1
        for mines in ((), (0,), (last,), (0, last)):
            traces = [
                (),
                (("click", 0),),
                (("mark", 0), ("click", 0)),
                (("click", last), ("click", 0)),
                (("click", 0), ("click", last)),
                (("click", n * n), ("mark", n * n)),
            ]
            if n <= 4 or (n == 10 and mines in ((), (last,))):
                traces.append(tuple(
                    ("click", i) for i in range(n * n) if i not in mines
                ))
            checks.extend((n, mines, trace) for trace in traces)
    # No safe squares: vacuous 'all safe opened' must NOT mean victory.
    for n in (2, 3):
        checks.append((n, tuple(range(n * n)), ()))
        checks.append((n, tuple(range(n * n)), (("click", 0),)))
    # A flag on a safe square prevents victory even if all other cells open.
    checks.append((2, (3,), (("mark", 0), ("click", 1), ("click", 2))))
    # A flag on a mine is allowed when every safe square is open.
    checks.append((2, (3,), (("mark", 3), ("click", 0), ("click", 1), ("click", 2))))
    return checks


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_step.bend as Step",
        "import ./nxn_victory.bend as Win", "",
        "def as_u32(ok: Bool) -> U32:",
        "  match ok:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0", "",
        "def same(actual: U32, want: U32) -> U32:",
        "  as_u32(U32.is_eq(actual, want))", "",
    ]
    for k, (n, mines, operations) in enumerate(checks):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  session = Step.new(board)")
        for action, index in operations:
            lines.append(f"  session = Step.{action}(session, {index})")
        lines.append(
            f"  same(Win.verdict(Win.inspect(session)), {int(expected(n, mines, operations))})"
        )
        lines.append("")
    for start in range(0, len(checks), 10):
        lines.append(f"def group_{start}() -> U32:")
        lines.append("  (" + " + ".join(
            f"case_{i}()" for i in range(start, min(start + 10, len(checks)))
        ) + " : U32)")
        lines.append("")
    lines.append("def main() -> U32:")
    lines.append("  (" + " + ".join(
        f"group_{i}()" for i in range(0, len(checks), 10)
    ) + " : U32)")
    return "\n".join(lines) + "\n"


def main():
    checks = cases()
    assert any(expected(n, mines, ops) for n, mines, ops in checks)
    assert any(not expected(n, mines, ops) for n, mines, ops in checks)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_victory.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N victory predicate: {len(checks)} cases / {args[-1]}", flush=True)
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
    print(f"PASS {len(checks)} independent Bend victory predicate checks")


if __name__ == "__main__":
    main()
