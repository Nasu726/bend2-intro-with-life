#!/usr/bin/env python3
"""Finite independent N x N lazy-first-click oracle. Not a uniform RNG test."""
from math import gcd
import os
from pathlib import Path
import subprocess
import tempfile
from test_nxn_full_game import expected as fixed_expected

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
         "nxn_clues.bend", "nxn_step.bend", "nxn_victory.bend",
         "nxn_terminal.bend", "nxn_neighbors.bend", "nxn_flood.bend",
         "nxn_lazy_game.bend")

def placed(n, count, seed, first):
    m = n*n - 1
    step = 1 + ((seed ^ 2654435769) % (m - 1))
    for _ in range(64):
        if gcd(step, m) == 1:
            break
        step = step % (m - 1) + 1
    else:
        step = 1
    offset = (seed ^ 2246822507) % m
    result = set()
    for i in range(count):
        compressed = (offset + i*step) % m
        cell = compressed if compressed < first else compressed + 1
        assert cell not in result and cell != first
        result.add(cell)
    assert len(result) == count
    return result

def invariant_checks():
    checks = 0
    for n in range(2, 101):
        for seed in (0, 1, 2, 20261028, 0xffffffff):
            for first in (0, n*n//2, n*n-1):
                for count in (0, 1, n*n//4, n*n//2, n*n-2, n*n-1):
                    a = placed(n, count, seed, first)
                    assert a == placed(n, count, seed, first)
                    assert len(a) == count and first not in a
                    checks += 1
    return checks

def expected(n, count, seed, operations, probe):
    if not (2 <= n <= 100 and 0 <= count < n*n):
        return 400
    first = next((i for action, i in operations
                  if action == "click" and 0 <= i < n*n), None)
    if first is None:
        return 300
    return fixed_expected(n, placed(n, count, seed, first), operations, probe)

def cases():
    out = []
    for n in (2, 3, 4, 10, 17):
        for seed in (0, 20261028):
            for count in (0, 1, n*n-1):
                first = (seed + count) % (n*n)
                second = (first + 1) % (n*n)
                out.append((n, count, seed,
                            (("mark", first), ("click", first)), first))
                out.append((n, count, seed,
                            (("click", first), ("click", second)), second))
    for n, count, seed, first in (
        (100, 5000, 123, 0), (100, 9000, 20261028, 5000),
        (10, 99, 1234, 99), (10, 0, 777, 0),
    ):
        out.append((n, count, seed, (("click", first),), first))
    out += [
        (1, 0, 0, (("click", 0),), 0),
        (101, 0, 0, (("click", 0),), 0),
        (10, 100, 0, (("click", 0),), 0),
        (2, 4, 0, (("click", 0),), 0),
        (10, 10, 111, (("mark", 0),), 0),
        (10, 10, 222, (("click", 100), ("mark", 0)), 0),
        (10, 10, 333, (("click", 127),), 0),
        (100, 9999, 0, (("click", 10000),), 0),
    ]
    return out

def generate_harness(checks):
    lines = ["import Base", "import ./nxn_lazy_game.bend as Lazy", "",
             "def equal(a: U32, b: U32) -> U32:",
             "  eq = U32.is_eq(a, b)", "  match eq:",
             "    case True{}:", "      1",
             "    case False{}:", "      0", ""]
    for k, (n, count, seed, ops, probe) in enumerate(checks):
        lines += [f"def case_{k}() -> U32:",
                  f"  g = Lazy.new({n}, {count}, {seed})"]
        lines += [f"  g = Lazy.{action}(g, {index})" for action, index in ops]
        lines += [f"  equal(Lazy.snapshot(g, {probe}), "
                  f"{expected(n, count, seed, ops, probe)})", ""]
    for a in range(0, len(checks), 10):
        lines += [f"def group_{a}() -> U32:",
                  "  (" + " + ".join(
                      f"case_{i}()" for i in range(a, min(a+10, len(checks)))
                  ) + " : U32)", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"group_{i}()" for i in range(0, len(checks), 10))
              + " : U32)"]
    return "\n".join(lines) + "\n"

def main():
    assert invariant_checks() == 8910
    checks = cases()
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        for name in FILES:
            (d / name).write_bytes((GAME / name).read_bytes())
        src = d / "check_lazy.bend"
        src.write_text(generate_harness(checks), encoding="utf-8")
        for cmd in (("bend", str(src), "--check-only"), ("bend", str(src))):
            p = subprocess.run(cmd, cwd=d, capture_output=True, text=True,
                               timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{cmd}\n{p.stdout}\n{p.stderr}")
            if len(cmd) == 2 and p.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(f"Expected {len(checks)} matches: {p.stdout}")
    print(f"PASS 8910 placement invariants and {len(checks)} Bend differential cases")

if __name__ == "__main__":
    main()
