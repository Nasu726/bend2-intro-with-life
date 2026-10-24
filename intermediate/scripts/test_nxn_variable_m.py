#!/usr/bin/env python3
"""Independent M=0..10 mine-row checks against Bend's N x N full game.

The Python oracle uses sets and deque BFS; Bend uses packed words and Array.
This tests a finite 10x10 family, not arbitrary N/M or a GUI.
"""
import os
from pathlib import Path
import subprocess
import tempfile

from test_nxn_full_game import FILES, expected

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def cases():
    # One first-click trace for every M, plus targeted flag/gap/win cases.
    # Full 10x10 floods are expensive under Bend's interpreter, so keep
    # this Bend/Python differential suite bounded rather than timing out CI.
    result = [(m, (("click", 0),), 99) for m in range(11)]
    result.extend((
        (9, (("click", 0), ("click", 99)), 99),
        (9, (("click", 0), ("click", 99), ("click", 59)), 59),
        (9, (("click", 0), ("mark", 99), ("click", 99)), 99),
        (10, (("click", 0), ("click", 99)), 99),
    ))
    return result


def source(checks):
    lines = [
        "import Base",
        "import ./nxn_mine_words.bend as Words",
        "import ./nxn_full_game.bend as Game",
        "import ./nxn_playthrough.bend as Demo",
        "",
        "def one_if_true(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0",
        "",
        "def one_if_equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))",
        "",
    ]
    for k, (m, operations, probe) in enumerate(checks):
        mines = tuple(range(50, 50 + m))
        lines.extend((
            f"def case_{k}() -> U32:",
            f"  board = Demo.mine_row({m}n, Words.new(10))",
            "  game = Game.new(board)",
        ))
        for action, index in operations:
            lines.append(f"  game = Game.{action}(game, {index})")
        lines.extend((
            f"  one_if_equal(Game.snapshot(game, {probe}), "
            f"{expected(10, mines, operations, probe)})",
            "",
        ))
    for start in range(0, len(checks), 8):
        lines.extend((
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(
                f"case_{i}()" for i in range(start, min(start + 8, len(checks)))
            ) + " : U32)",
            "",
        ))
    lines.extend((
        "def main() -> U32:",
        "  (" + " + ".join(
            f"group_{i}()" for i in range(0, len(checks), 8)
        ) + " : U32)",
    ))
    return "\n".join(lines) + "\n"


def check_oracle_examples():
    wall9 = tuple(range(50, 59))
    wall10 = tuple(range(50, 60))
    assert expected(10, (), (("click", 0),), 99) == 110
    assert expected(10, wall9, (("click", 0),), 99) == 0
    assert expected(10, wall9, (("click", 0), ("click", 99)), 99) == 10
    assert expected(10, wall9, (("click", 0), ("click", 99),
                                ("click", 59)), 59) == 111
    assert expected(10, wall10, (("click", 0), ("click", 99)), 99) == 110


def main():
    check_oracle_examples()
    checks = cases()
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in (*FILES, "nxn_playthrough.bend"):
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_variable_m.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            proc = subprocess.run(
                args, cwd=directory, capture_output=True, text=True,
                timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(
                    f"Expected {len(checks)} matches; got {proc.stdout}"
                )
    print(f"PASS {len(checks)} Bend/Python M=0..10 10x10 traces")


if __name__ == "__main__":
    main()
