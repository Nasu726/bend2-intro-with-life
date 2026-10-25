#!/usr/bin/env python3
"""Independent public-geometry oracle and Bend execution for six-bit masks.

A mask describes *unknown neighboring cell IDs* in a six-cell universe, not
actual mines. Invalid means no sound six-bit mapping, never a safe deduction.
"""
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ("nxn_geometry.bend", "nxn_neighbors.bend",
         "nxn_public_subset.bend", "nxn_public_neighbors.bend",
         "nxn_public_six_mask.bend")


def oracle(n, clue, revealed, universe):
    if len(universe) != 6 or clue not in revealed or not 2 <= n <= 100:
        return 64
    if (any(not 0 <= i < n*n or i in revealed for i in universe)
            or tuple(sorted(set(universe))) != universe):
        return 64
    if not 0 <= clue < n * n:
        return 64
    cx, cy = clue % n, clue // n
    unknown = tuple(i for i in range(n * n) if i not in revealed
                    and i != clue and abs(i % n - cx) <= 1
                    and abs(i // n - cy) <= 1)
    if not set(unknown).issubset(universe):
        return 64
    return sum(1 << universe.index(i) for i in unknown)


def cases():
    base = [
        (3, 0, (0, 2, 7), (1, 3, 4, 5, 6, 8)),
        (3, 2, (0, 2, 7), (1, 3, 4, 5, 6, 8)),
        (3, 7, (0, 2, 7), (1, 3, 4, 5, 6, 8)),
        (4, 0, (0, 1, 2, 4), (3, 5, 6, 7, 8, 9)),
        (4, 1, (0, 1, 2, 4), (3, 5, 6, 7, 8, 9)),
        (4, 2, (0, 1, 2, 4), (3, 5, 6, 7, 8, 9)),
        (4, 4, (0, 1, 2, 4), (3, 5, 6, 7, 8, 9)),
        (4, 3, (0, 1, 2, 4), (3, 5, 6, 7, 8, 9)),
        (3, 0, (0, 2, 7), (1, 3, 4, 5, 6)),
        (3, 7, (0, 2, 7), (1, 3, 4, 5, 6, 7)),
        (2, 0, (0,), (1, 2, 3)),
        (3, 0, (0, 2, 7), (0, 1, 3, 4, 5, 6)),
        (3, 0, (0, 2, 7), (1, 1, 3, 4, 5, 6)),
        (3, 0, (0, 2, 7), (1, 3, 4, 5, 6, 9)),
        (0, 0, (0,), (1, 2, 3, 4, 5, 6)),
        (3, 0, (0, 1, 2, 3, 4, 5, 6, 7, 8), (1, 3, 4, 5, 6, 8)),
    ]
    rng = random.Random(20261026)
    for n in (3, 4, 10):
        for _ in range(6):
            clue = rng.randrange(n * n)
            opened = set(rng.sample(range(n * n), min(5, n * n)))
            opened.add(clue)
            universe = tuple(sorted(rng.sample(range(n * n), 6)))
            base.append((n, clue, tuple(sorted(opened)), universe))
    assert [oracle(*case) for case in base[:7]] == [7, 13, 62, 2, 6, 15, 50]
    return base


def lit(items):
    return "[" + ", ".join(map(str, items)) + "]"


def program(batch):
    lines = ["import Base", "import ./nxn_public_six_mask.bend as Rule", ""]
    for i, (n, clue, opened, universe) in enumerate(batch):
        lines += [f"def case_{i}() -> U32:",
                  f"  Rule.tag(Rule.mask_for({n}, {clue}, "
                  f"{lit(opened)}, {lit(universe)}))", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"case_{i}()" for i in range(len(batch)))
              + " : U32)", ""]
    return "\n".join(lines)


def run_bend(path, expected):
    for check_only in (True, False):
        cmd = ["bend", str(path)] + (["--check-only"] if check_only else [])
        p = subprocess.run(cmd, cwd=path.parent, capture_output=True, text=True,
                           timeout=120, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if p.returncode:
            raise AssertionError(f"{cmd}: {p.stdout}\n{p.stderr}")
        if not check_only and p.stdout.strip().splitlines()[-1] != str(expected):
            raise AssertionError(f"{path.name}: expected {expected}, got {p.stdout}")


def main():
    checks = cases()
    if "--oracle-only" in sys.argv:
        assert all(0 <= oracle(*case) <= 64 for case in checks)
        print(f"PASS {len(checks)} independent public six-bit oracle cases")
        return
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in FILES:
            shutil.copyfile(ROOT / "minesweeper" / name, folder / name)
        run_bend(folder / "nxn_public_six_mask.bend", 7)
        for start in range(0, len(checks), 4):
            batch = checks[start:start + 4]
            file = folder / f"six_mask_{start}.bend"
            file.write_text(program(batch), encoding="utf-8")
            print(f"CHECK six-bit masks {start+1}-{start+len(batch)}", flush=True)
            run_bend(file, sum(oracle(*case) for case in batch))
    print(f"PASS {len(checks)} Bend/Python public six-bit masks")


if __name__ == "__main__":
    main()
