#!/usr/bin/env python3
"""Independent public-board oracle for the Bend three-clue/six-cell bridge.

Only public cell indices and numbers are passed to Bend. This finite test
checks the whole composition, not just the previously tested bitmask kernel.
"""
import itertools
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = (
    "nxn_geometry.bend", "nxn_neighbors.bend", "nxn_public_subset.bend",
    "nxn_public_neighbors.bend", "nxn_public_six_mask.bend",
    "nxn_public_three_small.bend", "nxn_public_three_bridge.bend",
)


def oracle(n, clues, revealed, universe, total, use_total):
    """Return the kernel's display score, or 0 for invalid/inconsistent input."""
    if not 2 <= n <= 100 or len(universe) != 6:
        return 0
    if (tuple(sorted(set(revealed))) != revealed
            or tuple(sorted(set(universe))) != universe
            or any(not 0 <= c < n * n for c in (*revealed, *universe, *(i for i, _ in clues)))
            or set(revealed) & set(universe)):
        return 0
    if use_total and n * n - len(revealed) != 6:
        return 0
    masks = []
    for cell, remaining in clues:
        if cell not in revealed:
            return 0
        x, y = cell % n, cell // n
        adjacent = {i for i in range(n * n) if i not in revealed
                    and i != cell and abs(i % n - x) <= 1
                    and abs(i // n - y) <= 1}
        if not adjacent.issubset(universe):
            return 0
        masks.append(sum(1 << j for j, i in enumerate(universe) if i in adjacent))
    models = [bits for bits in range(64)
              if all((bits & mask).bit_count() == remaining
                     for mask, (_, remaining) in zip(masks, clues))
              and (not use_total or bits.bit_count() == total)]
    if not models:
        return 0
    union = 0
    common = 63
    for bits in models:
        union |= bits
        common &= bits
    return len(models) * 100 + (63 ^ union) * 10 + common


def board_oracle(n, clues, revealed, universe, total, use_total):
    """Independent set-based public geometry enumeration (no bit masks)."""
    if (not 2 <= n <= 100 or len(universe) != 6
            or tuple(sorted(set(revealed))) != revealed
            or tuple(sorted(set(universe))) != universe
            or any(not 0 <= c < n*n for c in (*revealed, *universe))
            or set(revealed) & set(universe)
            or any(c not in revealed for c, _ in clues)
            or (use_total and n*n - len(revealed) != 6)):
        return 0
    for cell, _ in clues:
        x, y = cell % n, cell // n
        if any(i not in universe for i in range(n*n) if i not in revealed
               and abs(i % n - x) <= 1 and abs(i // n - y) <= 1):
            return 0
    candidates = []
    for count in range(7):
        for mine_tuple in itertools.combinations(universe, count):
            mines = set(mine_tuple)
            if use_total and len(mines) != total:
                continue
            if all(sum(abs(m % n - c % n) <= 1
                       and abs(m // n - c // n) <= 1 for m in mines) == remaining
                   for c, remaining in clues):
                candidates.append(mines)
    if not candidates:
        return 0
    certain_safe = set(universe) - set.union(*candidates)
    certain_mines = set.intersection(*candidates)
    safe_bits = sum(1 << i for i, cell in enumerate(universe) if cell in certain_safe)
    mine_bits = sum(1 << i for i, cell in enumerate(universe) if cell in certain_mines)
    return len(candidates) * 100 + safe_bits * 10 + mine_bits


def examples():
    base = [
        (3, ((0, 1), (2, 1), (7, 1)), (0, 2, 7), (1, 3, 4, 5, 6, 8), 2, True),
        (3, ((0, 1), (2, 1), (7, 1)), (0, 2, 7), (1, 3, 4, 5, 6, 8), 2, False),
        (3, ((0, 0), (2, 0), (7, 0)), (0, 2, 7), (1, 3, 4, 5, 6, 8), 0, True),
        (3, ((0, 1), (2, 1), (7, 8)), (0, 2, 7), (1, 3, 4, 5, 6, 8), 2, True),
        (3, ((0, 1), (2, 1), (1, 1)), (0, 2, 7), (1, 3, 4, 5, 6, 8), 2, True),
        (3, ((0, 1), (2, 1), (7, 1)), (0, 2, 7), (1, 3, 4, 5, 6), 2, True),
        (3, ((0, 1), (2, 1), (7, 1)), (0, 2, 7), (1, 3, 4, 5, 6, 7), 2, True),
        (3, ((0, 1), (2, 1), (7, 1)), (0, 2, 7), (1, 3, 4, 5, 6, 9), 2, True),
        (4, ((0, 0), (1, 0), (4, 1)), (0, 1, 2, 4), (3, 5, 6, 7, 8, 9), 0, False),
        (4, ((0, 0), (2, 1), (4, 1)), (0, 1, 2, 4), (3, 5, 6, 7, 8, 9), 0, False),
        (4, ((1, 0), (2, 1), (4, 1)), (0, 1, 2, 4), (3, 5, 6, 7, 8, 9), 0, False),
        (4, ((0, 0), (1, 0), (4, 1)), (0, 1, 2, 4), (3, 5, 6, 7, 8, 9), 2, True),
    ]
    assert oracle(*base[0]) == 341
    assert oracle(*base[1]) == 400
    assert oracle(*base[2]) == 730
    assert all(oracle(*case) == 0 for case in base[3:8])
    assert oracle(*base[11]) == 0
    return base


def lit(items):
    return "[" + ", ".join(map(str, items)) + "]"


def program(batch):
    lines = ["import Base", "import ./nxn_public_three_bridge.bend as Bridge",
             "import ./nxn_public_three_small.bend as Three", ""]
    for i, (n, clues, revealed, universe, total, use_total) in enumerate(batch):
        c0, c1, c2 = (cell for cell, _ in clues)
        r0, r1, r2 = (value for _, value in clues)
        flag = "True{}" if use_total else "False{}"
        lines.extend([f"def case_{i}() -> U32:",
                      f"  Three.score(Bridge.from_public({n}, {c0}, {c1}, {c2}, "
                      f"{r0}, {r1}, {r2}, {lit(revealed)}, {lit(universe)}, "
                      f"{total}, {flag}))", ""])
    lines.extend(["def main() -> U32:",
                  "  (" + " + ".join(f"case_{i}()" for i in range(len(batch)))
                  + " : U32)", ""])
    return "\n".join(lines)


def run_bend(path, expected):
    for check_only in (True, False):
        cmd = ["bend", str(path)] + (["--check-only"] if check_only else [])
        result = subprocess.run(cmd, cwd=path.parent, capture_output=True,
                                text=True, timeout=120,
                                env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if result.returncode:
            raise AssertionError(f"{cmd}: {result.stdout}\n{result.stderr}")
        if not check_only and result.stdout.strip().splitlines()[-1] != str(expected):
            raise AssertionError(f"{path.name}: expected {expected}, got {result.stdout}")


def main():
    checks = examples()
    assert all(oracle(*case) == board_oracle(*case) for case in checks)
    geometry = checks[0]
    for counts in itertools.product(range(4), repeat=3):
        clues = tuple((cell, count) for (cell, _), count in zip(geometry[1], counts))
        for total in range(7):
            for use_total in (False, True):
                assert oracle(3, clues, geometry[2], geometry[3], total, use_total) == board_oracle(
                    3, clues, geometry[2], geometry[3], total, use_total)
    if "--oracle-only" in sys.argv:
        print(f"PASS {len(checks)} bridge examples and 896 independent oracle conditions")
        return
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in DEPENDENCIES:
            shutil.copyfile(ROOT / "minesweeper" / name, folder / name)
        run_bend(folder / "nxn_public_three_bridge.bend", 341)
        for start in range(0, len(checks), 2):
            batch = checks[start:start + 2]
            file = folder / f"public_bridge_{start}.bend"
            file.write_text(program(batch), encoding="utf-8")
            print(f"CHECK three-clue bridge {start+1}-{start+len(batch)}", flush=True)
            run_bend(file, sum(oracle(*case) for case in batch))
    print(f"PASS {len(checks)} Bend/Python public three-clue bridge cases")


if __name__ == "__main__":
    main()
