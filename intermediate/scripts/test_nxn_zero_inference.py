#!/usr/bin/env python3
"""Finite Bend/Python differential checks for public zero-clue inference.

Only revealed zero clues imply safe neighbors. This is not a complete
N x N constraint solver or a no-guess generator.
"""
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def oracle(n, index, clue, opened, flags):
    if not 2 <= n <= 100 or not 0 <= index < n*n or clue != 0 or index not in opened:
        return ()
    x, y = index % n, index // n
    return tuple(
        row*n + col
        for row in range(max(0, y-1), min(n, y+2))
        for col in range(max(0, x-1), min(n, x+2))
        if (col, row) != (x, y)
        and row*n+col not in opened
        and row*n+col not in flags
    )


def cases():
    checks = set()
    for n in (0, 1, 2, 3, 4, 10, 17, 32, 100, 101):
        for index in (0, 1, n-1, n, n*n-1, n*n, 4294967295):
            if not 0 <= index <= 4294967295:
                continue
            checks.add((n, index, 0, (index,), ()))
            checks.add((n, index, 0, (), ()))
            checks.add((n, index, 1, (index,), ()))
    rng = random.Random(20261025)
    for n in (2, 3, 4, 10, 17, 32, 100):
        for _ in range(12):
            index = rng.randrange(n*n)
            x, y = index % n, index // n
            nearby = [row*n+col
                      for row in range(max(0, y-1), min(n, y+2))
                      for col in range(max(0, x-1), min(n, x+2))
                      if (col, row) != (x, y)]
            opened = tuple(sorted((index, *rng.sample(nearby, min(2, len(nearby))))))
            flags = tuple(sorted(rng.sample(nearby, min(2, len(nearby)))))
            checks.add((n, index, 0, opened, flags))
    checks.add((10, 0, 0, (0, 1), (10,)))
    return sorted(checks)


def literal(items):
    return "[" + ", ".join(map(str, items)) + "]" if items else "Nil{}"


def source(checks):
    lines = [
        "import Base", "import ./nxn_zero_inference.bend as Zero", "",
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
        "def one_if_true(value: Bool) -> U32:",
        "  match value:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
    ]
    for k, (n, index, clue, opened, flags) in enumerate(checks):
        lines.extend((
            f"def case_{k}() -> U32:",
            f"  one_if_true(same(Zero.safe_from_clue({n}, {index}, {clue}, "
            f"{literal(opened)}, {literal(flags)}), "
            f"{literal(oracle(n, index, clue, opened, flags))}))", "",
        ))
    for start in range(0, len(checks), 10):
        lines.extend((f"def group_{start}() -> U32:",
                      "  (" + " + ".join(
                          f"case_{i}()" for i in range(start, min(start+10, len(checks)))
                      ) + " : U32)", ""))
    lines.extend(("def main() -> U32:",
                  "  (" + " + ".join(f"group_{i}()" for i in range(0, len(checks), 10))
                  + " : U32)"))
    return "\n".join(lines) + "\n"


def main():
    checks = cases()
    assert oracle(10, 0, 0, (0,), ()) == (1, 10, 11)
    assert oracle(10, 0, 0, (0, 1), (10,)) == (11,)
    assert oracle(10, 0, 1, (0,), ()) == ()
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in ("nxn_geometry.bend", "nxn_neighbors.bend", "nxn_zero_inference.bend"):
            (folder / name).write_bytes((GAME / name).read_bytes())
        program = folder / "check_zero_inference.bend"
        program.write_text(source(checks), encoding="utf-8")
        for command in (("bend", str(program), "--check-only"),
                        ("bend", str(program))):
            proc = subprocess.run(command, cwd=folder, capture_output=True, text=True,
                                  timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if proc.returncode:
                raise AssertionError(f"{command}: {proc.stdout}\n{proc.stderr}")
            if len(command) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(f"Expected {len(checks)} exact matches: {proc.stdout}")
    print(f"PASS {len(checks)} public zero-clue Bend/Python checks")


if __name__ == "__main__":
    main()
