#!/usr/bin/env python3
"""Finite independent oracle and Bend execution for a six-cell three-clue kernel.

Each six-bit position is an unknown cell, NOT an internal mine board.
This verifies the bounded kernel; it does not certify a general N x N solver.
"""
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "minesweeper" / "nxn_public_three_small.bend"
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_three_clue_oracle import deductions

HIDDEN = (1, 3, 4, 5, 6, 8)


def oracle(a, b, c, ra, rb, rc, total, use_total):
    if any(mask < 0 or mask > 63 for mask in (a, b, c)):
        return 4, 0, 0, 0
    models = tuple(bits for bits in range(64)
                   if (bits & a).bit_count() == ra
                   and (bits & b).bit_count() == rb
                   and (bits & c).bit_count() == rc
                   and (not use_total or bits.bit_count() == total))
    if not models:
        return 4, 0, 0, 0
    union = 0
    common = 63
    for bits in models:
        union |= bits
        common &= bits
    return 1, 63 & ~union, common, len(models)


def public_cases():
    # Every hidden mine configuration of the same 3x3 public-clue geometry.
    checks = set()
    for bits in range(64):
        a, b, c = 7, 13, 62
        ra, rb, rc = ((bits & mask).bit_count() for mask in (a, b, c))
        for use_total in (True, False):
            checks.add((a, b, c, ra, rb, rc,
                        bits.bit_count() if use_total else 0, use_total))
    checks.update((
        (7, 13, 62, 1, 1, 1, 2, True),
        (7, 13, 62, 1, 1, 1, 0, False),
        (7, 13, 62, 1, 1, 1, 0, True),
        (7, 13, 62, 9, 1, 1, 2, True),
        (64, 13, 62, 1, 1, 1, 2, True),
        (7, 65, 62, 1, 1, 1, 2, True),
        (7, 13, 128, 1, 1, 1, 2, True),
    ))
    rng = random.Random(20261026)
    for _ in range(16):
        a, b, c, bits = (rng.randrange(64) for _ in range(4))
        checks.add((a, b, c, (bits & a).bit_count(),
                    (bits & b).bit_count(), (bits & c).bit_count(),
                    bits.bit_count(), True))
        checks.add((a, b, c, rng.randrange(7), rng.randrange(7),
                    rng.randrange(7), rng.randrange(7), True))
    return sorted(checks)


def source(checks):
    lines = [
        "import Base", "import ./nxn_public_three_small.bend as Rule", "",
        "def yes(b: Bool) -> U32:",
        "  match b:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def compare(+tag: U32, +expected_safe: U32, +expected_mines: U32,",
        "            +expected_models: U32, decision: Rule.Decision) -> U32:",
        "  match decision:",
        "    case Rule.Inconsistent{}:",
        "      yes(U32.is_eq(tag, 4))",
        "    case Rule.Forced{safe, mines, models}:",
        "      yes(Bool.and(U32.is_eq(tag, 1),",
        "        Bool.and(U32.is_eq(expected_safe, safe),",
        "          Bool.and(U32.is_eq(expected_mines, mines), U32.is_eq(expected_models, models)))))",
        "",
    ]
    for i, case in enumerate(checks):
        tag, safe, mines, count = oracle(*case)
        a, b, c, ra, rb, rc, total, use_total = case
        bool_literal = "True{}" if use_total else "False{}"
        lines += [
            f"def case_{i}() -> U32:",
            f"  compare({tag}, {safe}, {mines}, {count}, Rule.infer(",
            f"    {a}, {b}, {c}, {ra}, {rb}, {rc}, {total}, {bool_literal}))",
            "",
        ]
    for start in range(0, len(checks), 8):
        lines += [
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(f"case_{i}()" for i in
                            range(start, min(start + 8, len(checks)))) +
            " : U32)", "",
        ]
    lines += [
        "def main() -> U32:",
        "  (" + " + ".join(f"group_{i}()" for i in
                        range(0, len(checks), 8)) + " : U32)", "",
    ]
    return "\n".join(lines)


def cross_check_public_oracle():
    checked = 0
    for bits in range(64):
        clues = ((0, (bits & 7).bit_count()),
                 (2, (bits & 13).bit_count()),
                 (7, (bits & 62).bit_count()))
        for use_total in (True, False):
            total = bits.bit_count() if use_total else 0
            expected = oracle(7, 13, 62, clues[0][1], clues[1][1],
                              clues[2][1], total, use_total)
            status, safe, mines, count = deductions(
                3, total if use_total else None, clues)
            safe_bits = sum(1 << HIDDEN.index(i) for i in safe)
            mine_bits = sum(1 << HIDDEN.index(i) for i in mines)
            other = (1, safe_bits, mine_bits, count) if status == "ok" else (
                4, 0, 0, 0)
            assert expected == other, (bits, use_total, expected, other)
            checked += 1
    assert checked == 128
    assert oracle(7, 13, 62, 1, 1, 1, 2, True) == (1, 14, 1, 2)
    assert oracle(7, 13, 62, 1, 1, 1, 0, False) == (1, 10, 0, 3)
    print(f"PASS {checked} six-bit/whole-board independent public oracle checks",
          flush=True)


def run_bend(path, expected):
    for check_only in (True, False):
        args = ["bend", str(path)]
        if check_only:
            args.append("--check-only")
        result = subprocess.run(args, cwd=path.parent, capture_output=True,
                                text=True, timeout=120,
                                env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if result.returncode:
            raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
        if not check_only and result.stdout.strip().splitlines()[-1] != str(expected):
            raise AssertionError(f"{path.name}: expected {expected}, got {result.stdout}")


def main():
    cross_check_public_oracle()
    checks = public_cases()
    assert len(checks) >= 100
    assert {oracle(*case)[0] for case in checks} == {1, 4}
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        copied = folder / MODULE.name
        copied.write_bytes(MODULE.read_bytes())
        print("CHECK six-cell three-clue module / --check-only and run", flush=True)
        run_bend(copied, 341)
        # Combining all cases in one Bend main caused a 360s interpreter
        # timeout, despite successful typechecking and the 341 smoke result.
        # Independent four-case programs retain EVERY oracle comparison while
        # bounding Bend normalization cost and making failures attributable.
        batch_size = 4
        for start in range(0, len(checks), batch_size):
            batch = checks[start:start + batch_size]
            program = folder / f"check_nxn_public_three_{start}.bend"
            program.write_text(source(batch), encoding="utf-8")
            print(f"CHECK bounded three-clue cases {start + 1}-"
                  f"{start + len(batch)}/{len(checks)}", flush=True)
            run_bend(program, len(batch))
    print(f"PASS {len(checks)} bounded Bend/Python three-clue deductions")


if __name__ == "__main__":
    main()
