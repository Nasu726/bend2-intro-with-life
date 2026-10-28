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
        # Invalid click and pre-start flag must not choose the first cell.
        (10, 10, 8765, (("click", 100), ("click", 0)), 0),
        (10, 10, 8765, (("mark", 0), ("click", 127), ("click", 5)), 5),
        (10, 10, 8765, (), 0),
        # Minimal 2x2 full-mine-count boundary and terminal input stability.
        (2, 3, 20261029, (("click", 4), ("mark", 3), ("click", 1)), 1),
        (2, 3, 20261029, (("click", 1), ("click", 0)), 0),
    ]
    return out

def bend_cases():
    """Bounded executable sample, separate from the 77 Python-oracle traces.

    A 10,000-cell / 9,000-mine game requires thousands of Bend recursive
    allocations. Compiling 77 independent whole games in one Bend expression
    timed out at 360 seconds on CI #40727263508. Keep large-grid placement
    coverage in invariant_checks(), and execute small complete games here.
    """
    result = [
        # Complete 2x2 board, including zero cascade and terminal freeze.
        (2, 0, 0, (("click", 0),), 0),
        (2, 2, 0, (("click", 0),), 0),  # Active, not yet won.
        (2, 1, 20261028, (("click", 1), ("click", 2)), 2),  # Mine loss.
        (2, 3, 20261029, (("click", 1),), 1),
        (2, 3, 20261029, (("click", 4), ("mark", 3), ("click", 1)), 1),
        (2, 3, 20261029, (("click", 1), ("click", 0)), 0),
        # Full-neighbor boundaries and a nontrivial 3x3 mine count.
        (3, 8, 0, (("click", 0),), 0),
        (4, 15, 20261028, (("click", 0),), 0),
        # Bounded 10x10 packed-word path, avoiding a 10,000-cell cascade.
        (10, 99, 1234, (("click", 99),), 99),
        # No allocation may happen on pre-start flags or invalid clicks.
        (10, 10, 111, (("mark", 0),), 0),
        (10, 10, 222, (("click", 100), ("mark", 0)), 0),
        (10, 10, 8765, (), 0),
        # Invalid configurations must be rejected before board creation.
        (1, 0, 0, (("click", 0),), 0),
        (10, 100, 0, (("click", 0),), 0),
        (100, 9999, 0, (("click", 10000),), 0),
    ]
    assert len(result) == 15
    assert all(n <= 10 or not any(
        action == "click" and 0 <= i < n*n for action, i in ops
    ) for n, count, seed, ops, probe in result)
    return result


def generate_harness(checks):
    lines = ["import Base", "import ./nxn_lazy_game.bend as Lazy", "",
             "def one_if_true(ok: Bool) -> U32:",
             "  match ok:",
             "    case True{}:", "      1",
             "    case False{}:", "      0", "",
             "def equal(a: U32, b: U32) -> U32:",
             "  one_if_true(U32.is_eq(a, b))", ""]
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

def verify_prestart_contract():
    """Boundary actions do not select a first cell or alter Fresh."""
    assert len(cases()) == 77
    n, count, seed = 10, 10, 8765
    assert expected(n, count, seed, (), 0) == 300
    assert expected(n, count, seed, (("mark", 0), ("click", 127)), 0) == 300
    assert expected(n, count, seed, (("click", 100), ("click", 0)), 0) == (
        expected(n, count, seed, (("click", 0),), 0))
    assert expected(n, count, seed,
                    (("mark", 0), ("click", 127), ("click", 5)), 5) == (
        expected(n, count, seed, (("click", 5),), 5))

def main():
    assert invariant_checks() == 8910
    verify_prestart_contract()
    # All 77 reference traces remain available for oracle-level regression.
    reference = cases()
    assert len(reference) == 77
    phases = {expected(*trace) // 100 for trace in reference}
    assert phases == {0, 1, 2, 3, 4}, phases
    checks = bend_cases()
    assert {expected(*trace) // 100 for trace in checks} == {0, 1, 2, 3, 4}
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        for name in FILES:
            (d / name).write_bytes((GAME / name).read_bytes())
        # Split complete-game expressions to bound Bend compiler and evaluator
        # work. Each batch is independently typechecked and executed.
        for start in range(0, len(checks), 4):
            batch = checks[start:start + 4]
            src = d / f"check_lazy_{start}.bend"
            src.write_text(generate_harness(batch), encoding="utf-8")
            for cmd in (("bend", str(src), "--check-only"), ("bend", str(src))):
                print(f"CHECK lazy Bend cases {start + 1}-{start + len(batch)}"
                      f"/{len(checks)}: {'typecheck' if len(cmd) == 3 else 'run'}",
                      flush=True)
                p = subprocess.run(
                    cmd, cwd=d, capture_output=True, text=True, timeout=240,
                    env=dict(os.environ, BEND_NO_TELEMETRY="1"),
                )
                if p.returncode:
                    raise AssertionError(f"Batch {start}: {cmd}\n{p.stdout}\n{p.stderr}")
                if len(cmd) == 2 and p.stdout.strip().splitlines()[-1] != str(len(batch)):
                    raise AssertionError(
                        f"Batch {start}: expected {len(batch)} matches: {p.stdout}"
                    )
    print(f"PASS 8910 placement invariants, {len(reference)} reference traces, "
          f"and {len(checks)} bounded Bend differential cases")

if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--python-only"]:
        assert invariant_checks() == 8910
        verify_prestart_contract()
        assert len(bend_cases()) == 15
        assert {expected(*trace) // 100 for trace in cases()} == {0, 1, 2, 3, 4}
        assert {expected(*trace) // 100 for trace in bend_cases()} == {0, 1, 2, 3, 4}
        print("PASS 8910 independent Python placement invariants, 77 "
              "reference traces, 15 bounded Bend fixtures and pre-start contract")
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit("usage: test_nxn_lazy_game.py [--python-only]")
