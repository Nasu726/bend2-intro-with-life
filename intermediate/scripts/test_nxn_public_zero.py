#!/usr/bin/env python3
"""Finite differential test for public zero-clue deductions on N x N boards.

The Bend rule sees only revealed zero indices. The independent Python oracle
uses coordinates and true mines only to *check* soundness, never as Bend input.
This does not verify a complete no-guess solver, generator, or GUI.
"""
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def neighbors(n, index):
    if not 2 <= n <= 100 or not 0 <= index < n * n:
        return ()
    x, y = index % n, index // n
    return tuple(
        v * n + u
        for v in range(max(0, y - 1), min(n, y + 2))
        for u in range(max(0, x - 1), min(n, x + 2))
        if (u, v) != (x, y)
    )


def safe_from_zeros(n, zeros):
    return tuple(j for z in zeros for j in neighbors(n, z))


def cases():
    rng = random.Random(20261025)
    checks = []
    for n in (2, 3, 4, 10, 17, 100):
        # Choose actual zero clues, then place mines outside their neighborhoods.
        for k in range(1, 9):
            zeros = tuple(rng.randrange(n * n) for _ in range(k % 4 + 1))
            safe = set(zeros) | set(safe_from_zeros(n, zeros))
            candidates = [i for i in range(n * n) if i not in safe]
            mines = set(rng.sample(candidates, min(k, len(candidates))))
            assert not mines.intersection(safe)
            assert all(not mines.intersection(neighbors(n, z)) for z in zeros)
            checks.append((n, zeros, safe_from_zeros(n, zeros)))
    # Repeated observations, out-of-bounds/padding, empty lists, invalid sizes.
    checks.extend((n, zeros, safe_from_zeros(n, zeros)) for n, zeros in (
        (10, ()), (10, (0, 0, 1, 1)), (10, (99, 100, 127)),
        (100, (0, 9999, 10000, 4294967295)),
        (2, (0, 1, 2, 3)), (0, (0,)), (1, (0,)), (101, (0,)),
    ))
    return checks


def literal(values):
    return "[" + ", ".join(map(str, values)) + "]" if values else "Nil{}"


def source(checks):
    lines = [
        "import Base", "import ./nxn_public_zero.bend as Zero", "",
        "def same(a: List<U32>, b: List<U32>) -> Bool:",
        "  match a:", "    case Nil{}:",
        "      match b:", "        case Nil{}:", "          True{}",
        "        case y <> ys:", "          False{}",
        "    case x <> xs:", "      match b:",
        "        case Nil{}:", "          False{}",
        "        case y <> ys:",
        "          Bool.and(U32.is_eq(x, y), same(xs, ys))", "",
        "def one_if_true(b: Bool) -> U32:",
        "  match b:", "    case True{}:", "      1",
        "    case False{}:", "      0", "",
    ]
    for k, (n, zeros, expected) in enumerate(checks):
        lines.extend((
            f"def case_{k}() -> U32:",
            f"  one_if_true(same(Zero.proven_safe({n}, {literal(zeros)}), "
            f"{literal(expected)}))", "",
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
        "  (" + " + ".join(f"group_{i}()" for i in range(0, len(checks), 10))
        + " : U32)",
    ))
    return "\n".join(lines) + "\n"


def main():
    checks = cases()
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in ("nxn_geometry.bend", "nxn_neighbors.bend", "nxn_public_zero.bend"):
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_public_zero.bend"
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
                raise AssertionError(f"Expected {len(checks)} matches: {proc.stdout}")
    print(f"PASS {len(checks)} N x N public-zero Bend/Python checks")


if __name__ == "__main__":
    main()
