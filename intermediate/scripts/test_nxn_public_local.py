#!/usr/bin/env python3
"""Finite independent coordinate/set oracle for public N x N single-clue inference.

The Bend module receives NO hidden mine board. 'known_mines' means certified
mines, never arbitrary flags. Tests exact ordered indices and error handling.
Not a general solver, no-guess generator, GUI test, or universal proof.
"""
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("nxn_geometry.bend", "nxn_neighbors.bend", "nxn_public_local.bend")


def neighbors(n, index):
    if not 2 <= n <= 100 or not 0 <= index < n * n:
        return ()
    x, y = index % n, index // n
    return tuple(
        row * n + col
        for row in range(max(0, y - 1), min(n, y + 2))
        for col in range(max(0, x - 1), min(n, x + 2))
        if (col, row) != (x, y)
    )


def oracle(n, index, clue, mines, safe):
    if not 2 <= n <= 100 or not 0 <= index < n*n or not 0 <= clue <= 8:
        return 4, ()
    mines, safe = set(mines), set(safe)
    if index in mines:
        return 4, ()
    near = set(neighbors(n, index))
    if near & mines & safe:
        return 4, ()
    known = len(near & mines)
    unknown = tuple(sorted(near - mines - safe))
    remaining = clue - known
    if remaining < 0 or remaining > len(unknown):
        return 4, ()
    if not unknown:
        return 3, ()
    if remaining == 0:
        return 1, unknown
    if remaining == len(unknown):
        return 2, unknown
    return 3, ()


def cases():
    checks = [
        (3, 0, 1, (1,), ()),       # Known mine => two safe squares.
        (3, 4, 1, (), tuple(i for i in range(9) if i not in (4, 8))),
        (3, 0, 1, (1,), (1,)),     # Contradictory certifications.
        (3, 0, 0, (1,), ()),       # More certified mines than clue.
        (3, 0, 4, (), ()),        # Impossible corner clue.
        (3, 0, 0, (), (1, 3, 4)), # No remaining moves.
        (3, 0, 0, (0,), ()),       # Revealed clue cannot be a mine.
        (10, 100, 0, (), ()),     # Logical Array padding.
        (100, 10000, 0, (), ()),
        (1, 0, 0, (), ()),
        (101, 0, 0, (), ()),
    ]
    rng = random.Random(20261025)
    for n in (2, 3, 4, 10, 17, 100):
        for index in (0, n - 1, n, n*n//2, n*n-1):
            if index >= n*n:
                continue
            adjacent = neighbors(n, index)
            for _ in range(5):
                mines = tuple(i for i in adjacent if rng.randrange(4) == 0)
                safe = tuple(i for i in adjacent if rng.randrange(4) == 0)
                clue = rng.randrange(10)
                checks.append((n, index, clue, mines, safe))
    # Certified information outside the local neighborhood is irrelevant.
    checks.extend(((10, 0, 0, (99,), (98,)), (10, 0, 3, (), (99,))))
    return checks


def literal(values):
    return "[" + ", ".join(map(str, values)) + "]" if values else "Nil{}"


def source(checks):
    lines = [
        "import Base", "import ./nxn_public_local.bend as Rule", "",
        "def same(a: List<U32>, b: List<U32>) -> Bool:",
        "  match a:",
        "    case Nil{}:",
        "      match b:",
        "        case Nil{}:", "          True{}",
        "        case y <> ys:", "          False{}",
        "    case x <> xs:",
        "      match b:",
        "        case Nil{}:", "          False{}",
        "        case y <> ys:",
        "          Bool.and(U32.is_eq(x, y), same(xs, ys))", "",
        "def one_if_true(b: Bool) -> U32:",
        "  match b:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def compare(tag: U32, expected: List<U32>, decision: Rule.Decision) -> U32:",
        "  match decision:",
        "    case Rule.Safe{indices}:",
        "      one_if_true(Bool.and(U32.is_eq(tag, 1), same(indices, expected)))",
        "    case Rule.Mines{indices}:",
        "      one_if_true(Bool.and(U32.is_eq(tag, 2), same(indices, expected)))",
        "    case Rule.NoMove{}:",
        "      one_if_true(Bool.and(U32.is_eq(tag, 3), same(Nil{}, expected)))",
        "    case Rule.Inconsistent{}:",
        "      one_if_true(Bool.and(U32.is_eq(tag, 4), same(Nil{}, expected)))", "",
    ]
    for k, (n, index, clue, mines, safe) in enumerate(checks):
        tag, result = oracle(n, index, clue, mines, safe)
        lines.extend((
            f"def case_{k}() -> U32:",
            f"  compare({tag}, {literal(result)}, "
            f"Rule.infer({n}, {index}, {clue}, {literal(mines)}, {literal(safe)}))",
            "",
        ))
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
    tags = {oracle(*c)[0] for c in checks}
    assert tags == {1, 2, 3, 4}, tags
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_public_local.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N public local rule: {len(checks)} cases / {args[-1]}", flush=True)
            proc = subprocess.run(
                args, cwd=directory, capture_output=True, text=True,
                timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(
                    f"Expected {len(checks)} exact deductions; got {proc.stdout}"
                )
    print(f"PASS {len(checks)} independent N x N public local deductions")


if __name__ == "__main__":
    main()
