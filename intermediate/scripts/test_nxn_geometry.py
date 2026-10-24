#!/usr/bin/env python3
"""Finite independent N x N Bend geometry oracle; NOT a general proof."""
from pathlib import Path
import os
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "minesweeper" / "nxn_geometry.bend"


def cases():
    tests = []
    def add(expr, expected):
        tests.append(f"bit(U32.is_eq({expr}, {expected}))")
    def boolean(expr, expected):
        add(f"as_bit({expr})", int(expected))
    for n in (0, 1, 2, 3, 4, 10, 100, 101, 4294967295):
        boolean(f"Geo.valid_size({n})", 2 <= n <= 100)
    for n in (2, 3, 4, 10, 100):
        for x, y in ((0, 0), (n - 1, 0), (0, n - 1),
                     (n - 1, n - 1), (n // 2, n // 2),
                     (n, 0), (0, n), (4294967295, 0)):
            valid = x < n and y < n
            boolean(f"Geo.in_bounds({n}, {x}, {y})", valid)
            add(f"read_index(Geo.checked_index({n}, {x}, {y}))",
                y * n + x if valid else 10000)
        for i in (0, n - 1, n, n * n - 1, n * n, n * n + 27, 4294967295):
            boolean(f"Geo.valid_index({n}, {i})", i < n * n)
    for i in range(100, 128):
        boolean(f"Geo.valid_index(10, {i})", False)
    for y in range(10):
        if y < 9:
            boolean(f"Geo.neighbor(10, 9, {y}, 0, {y + 1})", False)
        for x in (0, 9):
            boolean(f"Geo.neighbor(10, {x}, {y}, {x}, {y})", False)
    rng = random.Random(20261019)
    for n in (2, 3, 4, 10):
        positions = list(range(n)) + [n, n + 1, 4294967295]
        for _ in range(55):
            x, y, u, v = (rng.choice(positions) for _ in range(4))
            expected = (x < n and y < n and u < n and v < n
                        and max(abs(x - u), abs(y - v)) == 1)
            boolean(f"Geo.neighbor({n}, {x}, {y}, {u}, {v})", expected)
    return tests


def bend_source(checks):
    groups = []
    for offset in range(0, len(checks), 8):
        groups.append(f"def group_{offset}() -> U32:\n  ("
                      + " + ".join(checks[offset:offset + 8]) + " : U32)")
    return ("import Base\nimport ./nxn_geometry.bend as Geo\n"
            "def bit(b: Bool) -> U32:\n  match b:\n"
            "    case True{}:\n      1\n    case False{}:\n      0\n"
            "def as_bit(b: Bool) -> U32:\n  bit(b)\n"
            "def read_index(m: Maybe<&2, U32>) -> U32:\n  match m:\n"
            "    case Some{i}:\n      i\n    case None{}:\n      10000\n\n"
            + "\n\n".join(groups)
            + "\n\ndef main() -> U32:\n  ("
            + " + ".join(f"group_{i}()" for i in range(0, len(checks), 8))
            + " : U32)\n")


def main():
    checks = cases()
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)
        (folder / "nxn_geometry.bend").write_bytes(MODULE.read_bytes())
        program = folder / "check_nxn.bend"
        program.write_text(bend_source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            p = subprocess.run(args, capture_output=True, text=True,
                               timeout=180, cwd=folder,
                               env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{args}: {p.stdout}\n{p.stderr}")
            if len(args) == 2:
                actual = p.stdout.strip().splitlines()[-1]
                if actual != str(len(checks)):
                    raise AssertionError(f"N x N geometry: {actual} != {len(checks)}")
    print(f"PASS Bend N x N geometry: {len(checks)} independent finite checks")


if __name__ == "__main__":
    main()
    # Keep geometry and bit-packed mine storage in the same N x N CI gate.
    from test_nxn_mine_words import main as verify_mine_words
    verify_mine_words()
    from test_nxn_clues import main as verify_nxn_clues
    verify_nxn_clues()
