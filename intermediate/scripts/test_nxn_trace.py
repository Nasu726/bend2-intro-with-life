#!/usr/bin/env python3
"""Compare Bend's typed N x N action replay with an independent Python BFS.

Finite checks only: no GUI, IO, all-board N=100 cascade, or general proof.
"""
import os
from pathlib import Path
import random
import subprocess
import tempfile
from test_nxn_full_game import expected, FILES

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def cases():
    checks = [
        (2, (), (), 0),
        (2, (), (("mark", 0),), 0),
        (2, (), (("click", 0),), 3),
        (2, (0,), (("click", 0),), 1),
        (2, (3,), (("click", 0), ("click", 3)), 3),
        (2, (0, 1, 2, 3), (("click", 0),), 0),
        (3, (8,), (("click", 0),), 8),
        (3, (8,), (("click", 0), ("mark", 7)), 7),
        (3, (0,), (("click", 0), ("mark", 1), ("click", 1)), 1),
        (3, (0,), (("click", 0), ("mark", 1), ("mark", 1), ("click", 1)), 1),
        (3, (8,), (("click", 0), ("click", 8)), 8),
        (10, (1,), (("click", 0), ("mark", 1)), 1),
        (10, (1,), (("click", 0), ("mark", 1), ("click", 1)), 1),
        (10, (1,), (("click", 0), ("mark", 1), ("mark", 1), ("click", 1)), 1),
        (10, (1,), (("click", 100), ("click", 0)), 0),
        (10, (1,), (("click", 127),), 0),
        (17, (1,), (("click", 0), ("mark", 1)), 1),
        (100, (1,), (("click", 0), ("mark", 1), ("click", 1)), 1),
        (100, (1,), (("click", 10000),), 0),
    ]
    rng = random.Random(20261025)
    for n in (2, 3, 4, 10, 17, 100):
        for _ in range(6):
            # A mine near the first click prevents expensive large zero floods.
            mines = tuple(sorted({1, rng.randrange(n * n)}))
            actions = (("click", 0),) + tuple(
                (rng.choice(("click", "mark")), rng.choice((0, 1, n * n - 1, n * n)))
                for _ in range(3)
            )
            checks.append((n, mines, actions, rng.choice((0, 1, n*n-1, n*n))))
    return checks


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_full_game.bend as Game",
        "import ./nxn_trace.bend as Trace", "",
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
        ops = ", ".join(
            f"Trace.{'Click' if action == 'click' else 'Mark'}{{{index}}}"
            for action, index in operations
        )
        lines.append(f"  game = Trace.replay([{ops}], Game.new(board))")
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
        for name in (*FILES, "nxn_trace.bend"):
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_trace.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N typed replay: {len(checks)} cases / {args[-1]}", flush=True)
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
    print(f"PASS {len(checks)} independent Bend N x N typed trace checks")


if __name__ == "__main__":
    main()
