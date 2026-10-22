#!/usr/bin/env python3
"""Finite Bend-vs-independent-set oracle for non-wrapping N x N clues.

This runs the Bend implementation; it is not a proof or a GUI/game test.
"""
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def expected(n, mines, i):
    # Reject invalid negative indices instead of interpreting them as cells.
    if not 0 <= i < n*n:
        return 0
    x, y = i % n, i // n
    return sum(j in mines for j in range(n*n) if j != i
               and max(abs(j % n - x), abs(j // n - y)) == 1)


def neighbor_ring(n, i):
    """A dense layout around one cell, excluding the cell itself.

    The set is built from bounded coordinates, not from expected(), so
    the finite Bend suite also reaches clue values 7 and 8.
    """
    x, y = i % n, i // n
    return tuple(sorted(yy*n + xx for yy in range(max(0, y-1), min(n, y+2))
                        for xx in range(max(0, x-1), min(n, x+2))
                        if (xx, yy) != (x, y)))


def check_expression(n, mines, index):
    """Render one Bend check, using the independent finite oracle."""
    state = f"Mines.new({n})"
    for cell in sorted(set(mines)):
        state = f"Mines.set_checked({state}, {cell}, True{{}})"
    want = expected(n, set(mines), index)
    return f"bit(U32.is_eq(Clues.read_count(Clues.clue({state}, {index})), {want}))"


def cases():
    checks = []
    for n in (2, 3, 4, 10, 17, 100):
        cells = n*n
        edge = {0, 1, n-1, n, n+1, cells//2, cells-1, 31, 32, 63, 64, 99}
        positions = sorted(i for i in edge if i < cells)
        layouts = [(), (0,), (cells-1,), (0, n+1), (n-1, n)]
        rng = random.Random(20261022 + n)
        for _ in range(2):
            layouts.append(tuple(sorted(rng.sample(range(cells), min(5, cells)))))
        def add_layout(mines, probes):
            for index in probes:
                checks.append(check_expression(n, mines, index))

        for mines in layouts:
            add_layout(mines, positions + [cells, cells+27, 4294967295])
        # Sparse layouts alone never exercise a clue of 8. Add full
        # rings and one-mine-short rings, but only probe the affected
        # cells so that Bend compilation remains a finite, bounded gate.
        for focus in (0, n+1):
            ring = neighbor_ring(n, focus)
            for dense in (ring, ring[1:]):
                add_layout(dense, (focus,))
        # Cross a U32 word boundary with all eight surrounding mines.
        # For n=10,17,100, the ring at boundary+n includes both bits
        # boundary and boundary+1 (31/32 and 63/64).
        if n in (10, 17, 100):
            for boundary in (31, 63):
                focus = boundary + n
                add_layout(neighbor_ring(n, focus), (focus,))
        # Full 0..8 spectrum and the self-mine exclusion rule. A mine on
        # the queried cell must never contribute to its own clue.
        if n in (3, 10):
            focus = n + 1
            ring = neighbor_ring(n, focus)
            for k in range(9):
                add_layout(ring[:k], (focus,))
                add_layout((*ring[:k], focus), (focus,))
    return list(dict.fromkeys(checks))


def program(checks):
    groups = []
    for i in range(0, len(checks), 3):
        groups.append(f"def group_{i}() -> U32:\n  (" + " + ".join(checks[i:i+3]) + " : U32)")
    return ("import Base\nimport ./nxn_geometry.bend as Geo\n"
            "import ./nxn_mine_words.bend as Mines\n"
            "import ./nxn_clues.bend as Clues\n"
            "def bit(b: Bool) -> U32:\n  match b:\n"
            "    case True{}:\n      1\n    case False{}:\n      0\n\n"
            + "\n\n".join(groups) + "\n\ndef main() -> U32:\n  ("
            + " + ".join(f"group_{i}()" for i in range(0, len(checks), 3))
            + " : U32)\n")


def main():
    checks = cases()
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)
        for name in ("nxn_geometry.bend", "nxn_mine_words.bend", "nxn_clues.bend"):
            shutil.copyfile(GAME / name, folder / name)
        entry = folder / "check_clues.bend"
        entry.write_text(program(checks), encoding="utf8")
        for args in (("bend", str(entry), "--check-only"), ("bend", str(entry))):
            p = subprocess.run(args, capture_output=True, text=True, timeout=240,
                               cwd=folder, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{args}: {p.stdout}\n{p.stderr}")
            if len(args) == 2 and p.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(f"N x N clues: {p.stdout} != {len(checks)}")
    print(f"PASS Bend N x N clues: {len(checks)} finite independent checks")


if __name__ == "__main__":
    main()
