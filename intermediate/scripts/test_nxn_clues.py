#!/usr/bin/env python3
"""Independent finite checks of Bend N x N neighbor mine counts."""
from pathlib import Path
import os
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MINE = ROOT / "minesweeper" / "nxn_mine_words.bend"
GEO = ROOT / "minesweeper" / "nxn_geometry.bend"
CLUES = ROOT / "minesweeper" / "nxn_clues.bend"


def oracle(n, mines, i):
    if not 0 <= i < n*n:
        return 99
    x, y = i % n, i // n
    return sum(j in mines for j in range(n*n)
               if max(abs(j % n-x), abs(j // n-y)) == 1)


def build_cases():
    rng = random.Random(20261024)
    boards = []
    for n in (2, 3, 4, 10, 17, 100):
        patterns = [set(), {0}, {n*n-1}, {0, n*n-1}]
        for _ in range(3):
            patterns.append(set(rng.sample(range(n*n), min(n*n, 1+n))))
        for mines in patterns:
            samples = sorted({0, 1, n-1, n, n*n-1, n*n, n*n+1,
                              2**32-1, *(rng.randrange(n*n) for _ in range(7))})
            boards.append((n, sorted(mines), samples))
    return boards


def bend_source(boards):
    lines = ["import Base", "import ./nxn_mine_words.bend as Words",
             "import ./nxn_clues.bend as Clues", "",
             "def bit(value: Bool) -> U32:",
             "  match value:",
             "    case True{}:",
             "      1",
             "    case False{}:",
             "      0", "",
             "def get_or_99(m: Maybe<&2, U32>) -> U32:",
             "  match m:",
             "    case Some{value}:",
             "      value",
             "    case None{}:",
             "      99", "",
             "def checked_bit(expected: U32, pair: Words.MineWords & Maybe<&2, U32>) -> U32:",
             "  (board, result) = pair",
             "  bit(U32.is_eq(get_or_99(result), expected))", ""]
    case_id = 0
    for n, mines, indices in boards:
        for i in indices:
            lines.append(f"def case_{case_id}() -> U32:")
            lines.append(f"  board = Words.new({n})")
            for j in mines:
                lines.append(f"  board = Words.set_checked(board, {j}, True{{}})")
            lines.append(f"  checked_bit({oracle(n, set(mines), i)}, Clues.count_checked(board, {i}))")
            lines.append("")
            case_id += 1
    lines.extend(["def main() -> U32:",
                  "  (" + " + ".join(f"case_{i}()" for i in range(case_id)) + " : U32)"])
    return "\n".join(lines) + "\n"


def main():
    boards = build_cases()
    expected = sum(len(indices) for _,_,indices in boards)
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for src in (MINE, GEO, CLUES):
            (folder / src.name).write_bytes(src.read_bytes())
        program = folder / "test_nxn_clues.bend"
        program.write_text(bend_source(boards), encoding="utf-8")
        for command in (("bend", str(program), "--check-only"),
                        ("bend", str(program))):
            proc = subprocess.run(command, capture_output=True, text=True,
                                  timeout=240, cwd=folder,
                                  env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if proc.returncode:
                raise AssertionError(f"{command}: {proc.stdout}\n{proc.stderr}")
            if len(command) == 2 and proc.stdout.strip().splitlines()[-1] != str(expected):
                raise AssertionError(f"clue mismatch: {proc.stdout} != {expected}")
    print(f"PASS Bend N x N clues: {expected} independent finite checks")


if __name__ == "__main__":
    main()
