#!/usr/bin/env python3
"""Independent exact oracle for the 4x4, two-mine public-information Bend solver.

Build one temporary Bend caller with many concrete public views. The oracle
does not import the game engine or use the Bend solver's bit operations.
"""
from itertools import combinations
from pathlib import Path
import os
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def neighbors(i):
    x, y = i % 4, i // 4
    return {j for j in range(16) if j != i and abs(x - j % 4) <= 1
            and abs(y - j // 4) <= 1}


def clues_for(mines, opened):
    return [(i, len(neighbors(i) & set(mines))) for i in opened]


def oracle(opened):
    """65536 means inconsistent; otherwise return safely openable bitmask."""
    if any(not (0 <= i < 16) or not (0 <= clue <= len(neighbors(i)))
           for i, clue in opened):
        return 65536
    valid = []
    for pair in combinations(range(16), 2):
        pair = set(pair)
        if all(i not in pair and len(neighbors(i) & pair) == clue
               for i, clue in opened):
            valid.append(pair)
    if not valid:
        return 65536
    all_possible = set().union(*valid)
    safe = set(range(16)) - all_possible - {i for i, _ in opened}
    return sum(1 << i for i in safe)


def cases():
    out = [[], [(0, 0)], [(0, 1)], [(0, 2)], [(0, 9)],
           [(0, 0), (0, 1)], [(16, 0)]]
    for mines, opened in (
        ({0, 5}, (1, 2, 3)),
        ({4, 15}, (0, 1, 5, 6)),
        ({6, 9}, (0, 5, 10, 15)),
        ({8, 14}, (1, 2, 3, 7)),
        ({2, 13}, (0, 4, 8, 12)),
        ({1, 11}, (0, 2, 3, 5, 7)),
    ):
        out.append(clues_for(mines, opened))
    out.extend([[(i, clue)] for i in range(16) for clue in (0, 1)])
    out.extend([
        [(0, 0), (15, 0)], [(0, 0), (15, 2)],
        [(0, 0), (0, 0)], [(15, 0), (15, 1)],
    ])
    return out


def program(items):
    defs = [
        "import Base",
        "import ./public_solver.bend as Solver",
        "def code(m: Maybe<&2, U32>) -> U32:",
        "  match m:",
        "    case Some{value}:",
        "      value",
        "    case None{}:",
        "      65536",
        "def bit(b: Bool) -> U32:",
        "  match b:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0",
    ]
    for k, opened in enumerate(items):
        data = ", ".join(f"Solver.Number{{{i}, {c}}}" for i, c in opened)
        target = oracle(opened)
        defs.extend([
            f"def check_{k}() -> U32:",
            f"  bit(U32.is_eq(code(Solver.provably_safe(Solver.Public{{[{data}]}})), {target}))",
        ])
    # Sum the checks in each bounded batch; no U32 bit-position encoding.
    groups = []
    for start in range(0, len(items), 8):
        name = f"group_{start // 8}"
        terms = " + ".join(f"check_{i}()" for i in range(start, min(start + 8, len(items))))
        defs.extend([f"def {name}() -> U32:", f"  ({terms} : U32)"])
        groups.append(f"{name}()")
    defs.extend(["def main() -> U32:", f'  ({" + ".join(groups)} : U32)'])
    return "\n".join(defs) + "\n"


def batches(items, size=4):
    """Partition every finite oracle case without discarding any checks."""
    if size < 1:
        raise ValueError("batch size must be positive")
    for start in range(0, len(items), size):
        yield start, items[start:start + size]


def main():
    items = cases()
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in ("public_solver.bend", "board4.bend", "board.bend", "game.bend"):
            shutil.copyfile(GAME / name, folder / name)
        env = dict(os.environ, BEND_NO_TELEMETRY="1")
        checked = 0
        # A single Bend main with 49 independent exact solver calls can
        # normalize for longer than the CI harness timeout. Keep all 49
        # oracle comparisons, but execute at most four per Bend program.
        for start, batch in batches(items):
            caller = folder / f"independent_public_oracle_{start:02d}.bend"
            caller.write_text(program(batch), encoding="utf-8")
            print(f"CHECK exact public solver {start + 1}-"
                  f"{start + len(batch)}/{len(items)}", flush=True)
            proc = subprocess.run(["bend", str(caller)], cwd=ROOT.parent,
                                  env=env, capture_output=True, text=True,
                                  timeout=120)
            if proc.returncode:
                raise AssertionError(
                    f"Exact public solver cases {start + 1}-"
                    f"{start + len(batch)} failed:\n{proc.stdout}\n{proc.stderr}")
            lines = proc.stdout.strip().splitlines()
            observed = lines[-1] if lines else "<no output>"
            if observed != str(len(batch)):
                raise AssertionError(
                    f"Independent public oracle cases {start + 1}-"
                    f"{start + len(batch)} passed {observed}/{len(batch)} checks")
            checked += len(batch)
        if checked != len(items):
            raise AssertionError(f"Only checked {checked}/{len(items)} cases")
        print(f"PASS {checked} independent public solver cases, including inconsistent views")

if __name__ == "__main__":
    main()
