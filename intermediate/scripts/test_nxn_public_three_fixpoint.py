#!/usr/bin/env python3
"""Finite public-only three-clue Bend fixed-point check against Python model.

The true mine locations appear ONLY in fixture preparation to calculate
revealed numbers; they never enter Bend inference. This is not an arbitrary
N x N solver, global satisfiability proof, or no-guess board generator.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("nxn_geometry.bend", "nxn_neighbors.bend", "nxn_public_local.bend",
         "nxn_public_three_fixpoint.bend")


def neighbors(n, index):
    return {other for other in range(n*n) if other != index
            and abs(other % n - index % n) <= 1
            and abs(other // n - index // n) <= 1}


def clues(n, opened, truth):
    return tuple((cell, len(neighbors(n, cell) & set(truth))) for cell in opened)


def model(n, public, mines=(), extra_safe=()):
    """Independent simultaneous-round oracle, with opened cells in safe."""
    shown = {cell for cell, _ in public}
    known_mines, known_safe = set(mines), set(extra_safe) | shown
    if len(shown) != 3 or known_mines & known_safe:
        return None
    if any(not 0 <= cell < n*n or not 0 <= value <= 8 for cell, value in public):
        return None
    for _ in range(25):
        new_mines, new_safe = set(), set()
        for cell, value in public:
            adjacent = neighbors(n, cell)
            unknown = adjacent - known_mines - known_safe
            residual = value - len(adjacent & known_mines)
            if residual < 0 or residual > len(unknown):
                return None
            if residual == 0:
                new_safe |= unknown
            if residual == len(unknown):
                new_mines |= unknown
        if new_mines & (known_safe | new_safe) or new_safe & known_mines:
            return None
        new_mines -= known_mines
        new_safe -= known_safe
        if not new_mines and not new_safe:
            return tuple(sorted(known_mines)), tuple(sorted(known_safe))
        known_mines |= new_mines
        known_safe |= new_safe
    raise AssertionError("three-clue fixed point did not converge in 25 rounds")


def fixtures():
    # (n, actual mines, revealed cells, independently certified mines, safe)
    data = (
        (3, (5, 7), (0, 2, 6), (), ()),
        (3, (), (0, 1, 6), (), ()),
        (4, (3, 15), (0, 1, 4), (), ()),
        (5, (12, 24), (0, 1, 5), (), (2, 3)),
        (10, (99,), (0, 1, 10), (), ()),
        (3, (5, 7), (0, 2, 6), (5,), ()),
    )
    result = []
    for n, truth, opened, known_mines, safe in data:
        public = clues(n, opened, truth)
        assert set(known_mines) <= set(truth)
        assert not set(safe) & set(truth)
        result.append((n, public, known_mines, safe))
    # Rejection contracts: out of range, absent public safe, duplicate clue,
    # impossible corner number, and conflicting certified evidence.
    result += [
        (3, ((0, 0), (2, 1), (9, 1)), (), ()),
        (3, ((0, 0), (2, 1), (6, 1)), (), (), "missing_public"),
        (3, ((0, 0), (0, 0), (6, 1)), (), ()),
        (3, ((0, 8), (2, 1), (6, 1)), (), ()),
        (3, ((0, 0), (2, 1), (6, 1)), (1,), ()),
    ]
    return result


def literal(items):
    return "[" + ", ".join(map(str, items)) + "]" if items else "Nil{}"


def source(cases):
    lines = [
        "import Base", "import ./nxn_public_three_fixpoint.bend as Fix",
        "import ./nxn_public_local.bend as Rule", "",
        "def count(items: List<&2, U32>) -> U32:",
        "  match items:", "    case Nil{}:", "      0",
        "    case item <> rest:", "      (1 + count(rest) : U32)", "",
        "def subset(items: List<&2, U32>, +got: List<&2, U32>) -> Bool:",
        "  match items:", "    case Nil{}:", "      True{}",
        "    case item <> rest:",
        "      Bool.and(Rule.contains(got, item), subset(rest, got))", "",
        "def bit(ok: Bool) -> U32:",
        "  match ok:", "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def valid(+expected_mines: List<&2, U32>, +expected_safe: List<&2, U32>,",
        "          result: Fix.Propagation) -> U32:",
        "  match result:",
        "    case Fix.Closure{+mines, +safe, changed}:",
        "      bit(Bool.and(U32.is_eq(count(mines), count(expected_mines)),",
        "          Bool.and(U32.is_eq(count(safe), count(expected_safe)),",
        "          Bool.and(subset(expected_mines, mines), subset(expected_safe, safe)))))",
        "    case Fix.Inconsistent{}:", "      0",
        "    case Fix.Limit{}:", "      0", "",
        "def invalid(result: Fix.Propagation) -> U32:",
        "  match result:",
        "    case Fix.Inconsistent{}:", "      1",
        "    case Fix.Limit{}:", "      0",
        "    case Fix.Closure{mines, safe, changed}:", "      0", "",
    ]
    for i, item in enumerate(cases):
        n, public, known_mines, safe = item[:4]
        safe_arg = tuple(sorted(set(safe) | {c for c, _ in public}))
        if len(item) == 5 and item[4] == "missing_public":
            safe_arg = safe
        expected = model(n, public, known_mines, safe)
        if len(item) == 5 and item[4] == "missing_public":
            expected = None
        params = ", ".join(map(str, (n, *sum(([c, v] for c, v in public), []))))
        call = f"Fix.infer_three({params}, {literal(known_mines)}, {literal(safe_arg)})"
        lines += [f"def case_{i}() -> U32:"]
        if expected is None:
            lines += [f"  invalid({call})", ""]
        else:
            lines += [f"  valid({literal(expected[0])}, {literal(expected[1])}, {call})", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"case_{i}()" for i in range(len(cases))) + " : U32)", ""]
    return "\n".join(lines)


def main():
    cases = fixtures()
    assert len(cases) == 11
    first = model(*cases[0])
    assert first == ((5, 7), (0, 1, 2, 3, 4, 6)), first
    assert model(*cases[5]) == first
    assert model(*cases[9]) is None
    print(f"PASS {len(cases)} Python three-clue fixture expectations", flush=True)
    if sys.argv[1:] == ["--model-only"]:
        return
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in FILES:
            (folder / name).write_bytes((GAME / name).read_bytes())
        program = folder / "check_three_fixpoint.bend"
        program.write_text(source(cases), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            proc = subprocess.run(args, cwd=folder, capture_output=True, text=True,
                                  timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(cases)):
                raise AssertionError(f"expected {len(cases)} matching cases: {proc.stdout}")
        example = GAME / "nxn_public_three_fixpoint.bend"
        proc = subprocess.run(("bend", str(example)), cwd=GAME,
                              capture_output=True, text=True, timeout=360,
                              env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if proc.returncode or proc.stdout.strip().splitlines()[-1] != "206":
            raise AssertionError(f"reader-independent fixed-point sample: {proc.stdout}\n{proc.stderr}")
    print(f"PASS {len(cases)} Bend three-clue fixed-point and rejection cases")


if __name__ == "__main__":
    main()
