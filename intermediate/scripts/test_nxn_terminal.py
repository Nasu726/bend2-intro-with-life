#!/usr/bin/env python3
"""Independent finite oracle for the N x N terminal-state *wrapper*.

No first-click relocation or zero cascade is assumed. The Python oracle
uses sets and coordinate arithmetic, not Bend's packed mine representation.
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
    "nxn_terminal.bend",
)


def expected(n, mines, operations, probe):
    mines = set(mines)
    opened, flags = {}, set()
    phase = 0  # Playing=0, Won=1, Lost=2
    for action, index in operations:
        if phase != 0 or not 0 <= index < n * n:
            continue
        if action == "mark":
            if index not in opened:
                if index in flags:
                    flags.remove(index)
                else:
                    flags.add(index)
        elif index not in opened and index not in flags:
            if index in mines:
                phase = 2
            else:
                x, y = index % n, index // n
                opened[index] = sum(
                    j in mines for j in range(n * n)
                    if j != index and abs(j % n - x) <= 1
                    and abs(j // n - y) <= 1
                )
                if len(mines) < n * n and len(opened) == n * n - len(mines):
                    phase = 1
    square = (10 + opened[probe] if probe in opened else
              1 if probe in flags else 0 if 0 <= probe < n*n else 99)
    return 100 * phase + square


def cases():
    checks = []
    for n in (2, 3, 4, 10, 17, 100):
        last = n*n - 1
        for mines in ((), (0,), (last,)):
            for operations, probe in (
                ((), 0),
                ((("click", 0),), 0),
                ((("mark", 0), ("click", 0)), 0),
                ((("click", last), ("mark", 0)), last),
                ((("click", n*n), ("mark", n*n)), 0),
            ):
                checks.append((n, mines, operations, probe))
    for n in (2, 3, 4):
        last = n*n - 1
        # Winning must freeze the board, even against a subsequent mine click.
        wins = tuple(("click", i) for i in range(last))
        checks.append((n, (last,), wins + (("click", last), ("mark", 0)), 0))
        # Flagging a safe square blocks victory until it is unflagged.
        checks.append((n, (last,), (("mark", 0),) +
                       tuple(("click", i) for i in range(1, last)), 0))
        checks.append((n, (last,), (("mark", 0),) +
                       tuple(("click", i) for i in range(1, last)) +
                       (("mark", 0), ("click", 0)), 0))
    checks.extend((
        (2, (0, 1, 2, 3), (("click", 0), ("mark", 1)), 0),
        (2, (3,), (("click", 3), ("click", 0), ("mark", 2)), 2),
        (10, (99,), (("click", 100), ("mark", 127)), 0),
        (10, (99,), (("click", 0), ("click", 99), ("mark", 1)), 1),
    ))
    return checks


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_terminal.bend as Terminal", "",
        "def one_if_bool(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0", "",
        "def one_if_equal(a: U32, b: U32) -> U32:",
        "  one_if_bool(U32.is_eq(a, b))", "",
    ]
    for k, (n, mines, operations, probe) in enumerate(checks):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  state = Terminal.new(board)")
        for action, index in operations:
            lines.append(f"  state = Terminal.{action}(state, {index})")
        lines.append(
            f"  one_if_equal(Terminal.snapshot(state, {probe}), "
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
    assert len(checks) == 103, len(checks)
    assert any(expected(n, mines, ops, p) // 100 == 1 for n, mines, ops, p in checks)
    assert any(expected(n, mines, ops, p) // 100 == 2 for n, mines, ops, p in checks)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_terminal.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N terminal wrapper: {len(checks)} cases / {args[-1]}", flush=True)
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
    print(f"PASS {len(checks)} independent Bend terminal-state checks")


if __name__ == "__main__":
    main()
