#!/usr/bin/env python3
"""Independent finite oracle and Bend 3x3 public exact-solver regression.

Run --oracle-only before committing; normal mode also typechecks and executes
Bend 2.0.39 on a bounded set of public-information cases.
"""
from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "minesweeper" / "nxn_public_exact3.bend"


def neighbors(index: int) -> set[int]:
    return {other for other in range(9)
            if other != index
            and abs(other // 3 - index // 3) <= 1
            and abs(other % 3 - index % 3) <= 1}


def oracle(clues: tuple[tuple[int, int], ...], total: int) -> tuple[int, int, int] | None:
    """Return safe mask, mine mask, model count; None means contradiction."""
    indices = [index for index, _ in clues]
    if total not in range(10) or len(set(indices)) != len(indices):
        return None
    if any(index not in range(9) or clue not in range(9) for index, clue in clues):
        return None
    hidden = tuple(i for i in range(9) if i not in indices)
    models = []
    for mines in combinations(hidden, total):
        mine_set = set(mines)
        if all(len(mine_set & neighbors(index)) == clue for index, clue in clues):
            models.append(mine_set)
    if not models:
        return None
    union = set.union(*models)
    intersection = set.intersection(*models)
    safe = set(hidden) - union
    bits = lambda cells: sum(1 << i for i in cells)
    return bits(safe), bits(intersection), len(models)


CASES = (
    (((0, 1), (2, 1), (7, 1)), 2),  # three-clue gap
    (((0, 1), (2, 1), (7, 1)), 1),  # global total changes the answer
    (((0, 1), (2, 1), (7, 1)), 0),  # inconsistent total
    (((0, 1), (2, 1), (7, 1)), 3),  # inconsistent total
    (((0, 0),), 1),
    (((0, 1),), 1),
    (((0, 0), (8, 0)), 1),
    ((), 0),
    ((), 9),
    (((0, 1), (0, 1)), 1),  # duplicate clue
    (((9, 0),), 1),  # invalid index
    (((0, 9),), 1),  # invalid clue
    ((), 10),  # invalid total
)


def literal(clues: tuple[tuple[int, int], ...]) -> str:
    if not clues:
        return "Nil{}"
    return "[" + ", ".join(f"Exact.Number{{{i}, {n}}}" for i, n in clues) + "]"


def bend_test_source() -> str:
    lines = [
        "import Base", "import ./nxn_public_exact3.bend as Exact", "",
        "def equals(actual: Exact.Decision, +safe: U32, +mines: U32,",
        "           +models: U32, +inconsistent: Bool) -> U32:",
        "  match actual:",
        "    case Exact.Inconsistent{}:",
        "      one_if(inconsistent)",
        "    case Exact.Deduced{s, m, count}:",
        "      one_if(Bool.and(Bool.not(inconsistent),",
        "        Bool.and(U32.is_eq(s, safe),",
        "          Bool.and(U32.is_eq(m, mines), U32.is_eq(count, models)))))", "",
        "def one_if(yes: Bool) -> U32:",
        "  match yes:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
    ]
    for k, (clues, total) in enumerate(CASES):
        expected = oracle(clues, total)
        safe, mines, count = expected if expected is not None else (0, 0, 0)
        invalid = "True{}" if expected is None else "False{}"
        lines += [f"def case_{k}() -> U32:",
                  f"  equals(Exact.infer({literal(clues)}, {total}),",
                  f"         {safe}, {mines}, {count}, {invalid})", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"case_{i}()" for i in range(len(CASES))) + " : U32)", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-only", action="store_true")
    args = parser.parse_args()
    assert oracle(((0, 1), (2, 1), (7, 1)), 2) == (56, 2, 2)
    assert oracle(((0, 1), (2, 1), (7, 1)), 1) == (362, 16, 1)
    assert oracle(((0, 1), (2, 1), (7, 1)), 0) is None
    assert oracle((), 0) == (511, 0, 1)
    assert oracle((), 9) == (0, 511, 1)
    assert len(CASES) == 13
    if args.oracle_only:
        print(f"PASS independent Python oracle: {len(CASES)} cases")
        return
    with tempfile.TemporaryDirectory() as folder:
        dest = Path(folder)
        for name in ("nxn_public_exact3.bend", "nxn_neighbors.bend", "nxn_geometry.bend"):
            shutil.copyfile(MODULE.parent / name, dest / name)
        program = dest / "check_nxn_public_exact3.bend"
        program.write_text(bend_test_source(), encoding="utf-8")
        for cmd in (("bend", str(program), "--check-only"), ("bend", str(program))):
            result = subprocess.run(cmd, cwd=dest, capture_output=True, text=True,
                                    timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if result.returncode:
                raise AssertionError(f"{cmd}: {result.stdout}\n{result.stderr}")
            if len(cmd) == 2 and result.stdout.strip().splitlines()[-1] != str(len(CASES)):
                raise AssertionError(f"Expected {len(CASES)}; got {result.stdout}")
    print(f"PASS {len(CASES)} independent 3x3 public exact Bend deductions")


if __name__ == "__main__":
    main()
