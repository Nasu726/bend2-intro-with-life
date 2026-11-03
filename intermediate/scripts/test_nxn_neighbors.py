#!/usr/bin/env python3
"""Exact ordered-list differential test for Bend's N x N neighbor frontier.

Independent Python coordinate oracle; this does NOT test flood, game state,
victory, or any universal proof. Includes invalid logical/padding indices.
"""
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def oracle(n, index):
    if not 2 <= n <= 100 or not 0 <= index < n * n:
        return ()
    x, y = index % n, index // n
    return tuple(
        v * n + u
        for v in range(max(0, y - 1), min(n, y + 2))
        for u in range(max(0, x - 1), min(n, x + 2))
        if (u, v) != (x, y)
    )


def cases():
    checks = set()
    for n in (0, 1, 2, 3, 4, 10, 17, 32, 100, 101):
        for i in (0, 1, n - 1, n, n + 1, n * n - 1,
                  n * n, n * n + 1, 4294967295):
            if 0 <= i <= 4294967295:
                checks.add((n, i))
    for n in (2, 3, 4, 10, 17, 32, 100):
        for y in (0, 1, n // 2, n - 2, n - 1):
            for x in (0, 1, n // 2, n - 2, n - 1):
                checks.add((n, y * n + x))
    # 10x10 Array capacity is 128; slots 100..127 are NOT valid cells.
    checks.update((10, i) for i in range(100, 128))
    rng = random.Random(20261024)
    for n in (2, 3, 4, 10, 17, 32, 100):
        for _ in range(12):
            checks.add((n, rng.randrange(n * n)))
    return sorted(checks)


def literal(values):
    return "[" + ", ".join(map(str, values)) + "]" if values else "Nil{}"


def source(checks):
    lines = [
        "import Base", "import ./nxn_neighbors.bend as Neighbors", "",
        "def same(a: List<U32>, b: List<U32>) -> Bool:",
        "  match a:",
        "    case Nil{}:",
        "      match b:",
        "        case Nil{}:",
        "          True{}",
        "        case y <> ys:",
        "          False{}",
        "    case x <> xs:",
        "      match b:",
        "        case Nil{}:",
        "          False{}",
        "        case y <> ys:",
        "          Bool.and(U32.is_eq(x, y), same(xs, ys))", "",
        "def one_if_true(b: Bool) -> U32:",
        "  match b:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0", "",
    ]
    for k, (n, index) in enumerate(checks):
        lines.extend((
            f"def case_{k}() -> U32:",
            f"  one_if_true(same(Neighbors.neighbors({n}, {index}), "
            f"{literal(oracle(n, index))}))",
            "",
        ))
    for start in range(0, len(checks), 10):
        lines.extend((
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(
                f"case_{i}()" for i in range(start, min(start + 10, len(checks)))
            ) + " : U32)",
            "",
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
        for name in ("nxn_geometry.bend", "nxn_neighbors.bend"):
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_neighbors.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N ordered neighbors: {len(checks)} cases / {args[-1]}", flush=True)
            proc = subprocess.run(
                args, cwd=directory, capture_output=True, text=True,
                timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(
                    f"Expected {len(checks)} exact list matches; got {proc.stdout}"
                )
    print(f"PASS {len(checks)} independent ordered N x N neighbor checks")


if __name__ == "__main__":
    main()
