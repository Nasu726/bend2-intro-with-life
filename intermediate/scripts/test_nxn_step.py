#!/usr/bin/env python3
"""Finite independent differential checks for Bend's ACTIVE one-cell N x N step.

This deliberately does not test first-click relocation, zero flood or victory.
The Python oracle uses sets and coordinate arithmetic, not U32 word operations.
"""
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
         "nxn_clues.bend", "nxn_step.bend")


def expected(n, mines, operations, probe):
    opened, flags, lost = {}, set(), False
    for action, index in operations:
        if lost or not 0 <= index < n*n:
            continue
        if action == "mark":
            if index not in opened:
                if index in flags:
                    flags.remove(index)
                else:
                    flags.add(index)
        elif index not in flags and index not in opened:
            if index in mines:
                lost = True
            else:
                x, y = index % n, index // n
                opened[index] = sum(
                    j in mines for j in range(n*n)
                    if j != index and abs(j % n-x) <= 1
                    and abs(j // n-y) <= 1)
    code = (10 + opened[probe] if probe in opened else
            1 if probe in flags else 0 if 0 <= probe < n*n else 99)
    return (200 if lost else 0) + code


def cases():
    rng = random.Random(20261024)
    result = []
    for n in (2, 3, 4, 10, 17, 100):
        last = n*n - 1
        mine_sets = (set(), {1}, {last}, {0, last})
        for mines in mine_sets:
            for operations, probe in (
                ([("click", 0)], 0),
                ([("click", last)], last),
                ([("mark", last), ("click", last)], last),
                ([("mark", last), ("mark", last), ("click", last)], last),
                ([("click", n*n), ("mark", n*n)], 0),
                ([("click", last), ("mark", 0)], 0),
            ):
                result.append((n, mines, operations, probe))
        # Array padding must not alias a logical square.
        padding = 1 << (n*n-1).bit_length()
        if padding > n*n:
            result.append((n, {0}, [("click", n*n), ("mark", padding-1)], 0))
        # Include a few non-toroidal row-boundary cases.
        result.append((n, {n-1}, [("click", n)], n))
        # Keep the N=100 compiler workload bounded.
        if n != 100:
            for _ in range(8):
                mines = set(rng.sample(range(n*n), min(3, n*n-1)))
                probe = rng.randrange(n*n)
                ops = [(rng.choice(("mark", "click")), rng.randrange(n*n+2))
                       for _ in range(3)]
                result.append((n, mines, ops, probe))
    return result


def source(all_cases):
    lines = ["import Base", "import ./nxn_mine_words.bend as Words",
             "import ./nxn_step.bend as Step", "",
             "def one_if_true(equal: Bool) -> U32:",
             "  match equal:",
             "    case True{}:",
             "      1",
             "    case False{}:",
             "      0", "",
             "def one_if_equal(a: U32, b: U32) -> U32:",
             "  one_if_true(U32.is_eq(a, b))", ""]
    for k, (n, mines, operations, probe) in enumerate(all_cases):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for index in sorted(mines):
            lines.append(f"  board = Words.set_checked(board, {index}, True{{}})")
        lines.append("  s = Step.new(board)")
        for action, index in operations:
            method = "mark" if action == "mark" else "click"
            lines.append(f"  s = Step.{method}(s, {index})")
        want = expected(n, mines, operations, probe)
        lines.append(f"  one_if_equal(Step.snapshot(s, {probe}), {want})")
        lines.append("")
    lines.append("def main() -> U32:")
    lines.append("  (" + " + ".join(f"case_{i}()" for i in range(len(all_cases))) + " : U32)")
    return "\n".join(lines) + "\n"


def main():
    all_cases = cases()
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        path = directory / "check_nxn_step.bend"
        path.write_text(source(all_cases), encoding="utf-8")
        for args in (("bend", str(path), "--check-only"),
                     ("bend", str(path))):
            print(f"CHECK active N x N step: {len(all_cases)} cases / {args[-1]}", flush=True)
            proc = subprocess.run(args, cwd=directory, capture_output=True,
                                  text=True, timeout=360,
                                  env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(all_cases)):
                raise AssertionError(f"Expected {len(all_cases)} independent matches, got {proc.stdout}")
    print(f"PASS {len(all_cases)} independent Bend active-step checks")


if __name__ == "__main__":
    main()
