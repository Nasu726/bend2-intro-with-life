#!/usr/bin/env python3
"""Independent finite model-check for the Bend two-clue subset kernel.

Inputs are already derived public unknown-neighbor sets with no duplicates.
Brute-force all mine assignments, rather than implementing subtraction logic
as the oracle. Non-nested cases are intentionally allowed to return NoMove.
"""
import itertools
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "minesweeper" / "nxn_public_subset.bend"


def oracle(a, b, ra, rb):
    a, b = set(a), set(b)
    if ra > len(a) or rb > len(b):
        return 4, ()
    # The kernel deliberately declines non-nested constraints.
    if not (a <= b or b <= a):
        return 3, ()
    union = sorted(a | b)
    solutions = [
        set(i for i, chosen in zip(union, bits) if chosen)
        for bits in itertools.product((False, True), repeat=len(union))
        if sum(chosen for i, chosen in zip(union, bits) if i in a) == ra
        and sum(chosen for i, chosen in zip(union, bits) if i in b) == rb
    ]
    if not solutions:
        return 4, ()
    diff = tuple(sorted((b - a) if a <= b else (a - b)))
    if not diff:
        return 3, ()
    if all(not (set(diff) & s) for s in solutions):
        return 1, diff
    if all(set(diff) <= s for s in solutions):
        return 2, diff
    return 3, ()


def cases():
    cases = [
        ((3, 4), (2, 3, 4, 5), 1, 1),  # 3x3 public clues at 0 and 1.
        ((3, 4), (2, 3, 4, 5), 1, 3),  # Difference cells are mines.
        ((3, 4), (2, 3, 4, 5), 1, 0),  # Contradictory nested counts.
        ((3, 4), (2, 3, 4, 5), 1, 4),
        ((1, 2), (1, 2), 1, 1),
        ((1, 2), (1, 2), 1, 2),
        ((1, 2), (2, 3), 1, 1),       # Overlap without containment.
        ((), (7,), 0, 0),
        ((), (7,), 0, 1),
        ((1,), (1, 2), 2, 1),
        ((1, 2), (1,), 1, 1),
        ((1, 2, 3), (1, 2), 1, 1),
        ((1, 2, 3), (1, 2), 2, 1),
    ]
    rng = random.Random(20261025)
    universe = tuple(range(1, 8))
    for k in range(108):
        a = set(i for i in universe if rng.randrange(3) == 0)
        b = set(i for i in universe if rng.randrange(3) == 0)
        if k % 3 == 0:
            a &= b
        elif k % 3 == 1:
            b &= a
        a, b = tuple(sorted(a)), tuple(sorted(b))
        cases.append((a, b, rng.randrange(len(a) + 2), rng.randrange(len(b) + 2)))
    return cases


def literal(values):
    return "[" + ", ".join(map(str, values)) + "]" if values else "Nil{}"


def source(cases):
    lines = [
        "import Base", "import ./nxn_public_subset.bend as Rule", "",
        "def same(a: List<U32>, b: List<U32>) -> Bool:",
        "  match a:",
        "    case Nil{}:",
        "      match b:",
        "        case Nil{}:", "          True{}",
        "        case y <> ys:", "          False{}",
        "    case x <> xs:",
        "      match b:",
        "        case Nil{}:", "          False{}",
        "        case y <> ys:",
        "          Bool.and(U32.is_eq(x, y), same(xs, ys))", "",
        "def one_if_true(b: Bool) -> U32:",
        "  match b:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def compare(tag: U32, expected: List<U32>, result: Rule.Decision) -> U32:",
        "  match result:",
        "    case Rule.Safe{indices}:",
        "      one_if_true(Bool.and(U32.is_eq(tag, 1), same(indices, expected)))",
        "    case Rule.Mines{indices}:",
        "      one_if_true(Bool.and(U32.is_eq(tag, 2), same(indices, expected)))",
        "    case Rule.NoMove{}:",
        "      one_if_true(Bool.and(U32.is_eq(tag, 3), same(Nil{}, expected)))",
        "    case Rule.Inconsistent{}:",
        "      one_if_true(Bool.and(U32.is_eq(tag, 4), same(Nil{}, expected)))", "",
    ]
    for i, (a, b, ra, rb) in enumerate(cases):
        tag, result = oracle(a, b, ra, rb)
        lines += [
            f"def case_{i}() -> U32:",
            f"  compare({tag}, {literal(result)}, Rule.infer("
            f"{literal(a)}, {literal(b)}, {ra}, {rb}))", "",
        ]
    for start in range(0, len(cases), 8):
        lines += [
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(f"case_{i}()" for i in range(start, min(start+8, len(cases)))) + " : U32)",
            "",
        ]
    lines += [
        "def main() -> U32:",
        "  (" + " + ".join(f"group_{i}()" for i in range(0, len(cases), 8)) + " : U32)",
        "",
    ]
    return "\n".join(lines)


def main():
    checks = cases()
    assert len(checks) == 121
    assert {oracle(*case)[0] for case in checks} == {1, 2, 3, 4}
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        (folder / MODULE.name).write_bytes(MODULE.read_bytes())
        program = folder / "check_nxn_public_subset.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"), ("bend", str(program))):
            print(f"CHECK two public constraints: {len(checks)} / {args[-1]}", flush=True)
            result = subprocess.run(args, cwd=folder, capture_output=True,
                                    text=True, timeout=360,
                                    env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if result.returncode:
                raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
            if len(args) == 2 and result.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(f"Expected {len(checks)}; got {result.stdout}")
    print(f"PASS {len(checks)} finite two-constraint deductions")


if __name__ == "__main__":
    main()
