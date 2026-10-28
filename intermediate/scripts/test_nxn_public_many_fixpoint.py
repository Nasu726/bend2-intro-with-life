#!/usr/bin/env python3
"""Any-count Bend public-clue propagation vs independent synchronous Python.

Only revealed numbers and *certified* safe/mine sets go to Bend; true layouts
are used solely to produce revealed clues for finite fixtures. Not a full
constraint solver, proof of N x N completeness, or no-guess generator.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("nxn_geometry.bend", "nxn_neighbors.bend", "nxn_public_local.bend",
         "nxn_public_three_fixpoint.bend", "nxn_public_many_fixpoint.bend")


def neighbors(n, index):
    return {other for other in range(n*n) if other != index
            and abs(other % n - index % n) <= 1
            and abs(other // n - index // n) <= 1}


def public_from_truth(n, mine_truth, opened):
    return tuple((i, len(neighbors(n, i) & set(mine_truth))) for i in opened)


def model(n, public, known_mines=(), known_safe=(), fuel=None):
    """Independent synchronous-round oracle. Returns None on bad evidence."""
    if type(n) is not int or not 2 <= n <= 100:
        return None
    if fuel is None:
        fuel = n*n+1
    if type(fuel) is not int or fuel < 0:
        return None
    cells = [i for i, _ in public]
    if len(cells) != len(set(cells)):
        return None
    mines, safe = set(known_mines), set(known_safe)
    if any(type(i) is not int or i < 0 or i >= n*n for i in (*known_mines, *known_safe)):
        return None
    if tuple(known_mines) != tuple(sorted(mines)):
        return None
    if tuple(known_safe) != tuple(sorted(safe)):
        return None
    if mines & safe or not set(cells) <= safe:
        return None
    if any(type(i) is not int or type(v) is not int
           or i < 0 or i >= n*n or v < 0 or v > 8 for i, v in public):
        return None
    for _ in range(fuel):
        new_mines, new_safe = set(), set()
        for index, value in public:
            around = neighbors(n, index)
            unknown = around - mines - safe
            remaining = value - len(mines & around)
            if not 0 <= remaining <= len(unknown):
                return None
            if remaining == 0:
                new_safe |= unknown
            if remaining == len(unknown):
                new_mines |= unknown
        if new_mines & (safe | new_safe) or new_safe & mines:
            return None
        new_mines -= mines
        new_safe -= safe
        if not new_mines and not new_safe:
            return tuple(sorted(mines)), tuple(sorted(safe))
        mines |= new_mines
        safe |= new_safe
    return "Limit"


def fixtures():
    data = [
        # (size, true mines, revealed, externally certified mines, safe, fuel)
        (3, (0,), (1,2,4,5), (), (), 10),
        (3, (5,7), (0,2,6), (), (), 10),
        (3, (5,7), (0,2), (), (), 10),
        (3, (5,7), (0,), (), (), 10),
        (3, (5,7), (), (), (), 1),
        (4, (3,15), (0,1,4,5,8), (), (), 17),
        (5, (12,24), (0,1,5,6,10), (), (2,3), 26),
        (10, (99,), (0,1,10,11,20,21), (), (), 101),
        (3, (0,), (1,2,4,5), (0,), (), 10),
        (3, (5,7), (0,2,6), (), (), 1),
        # Fully safe boards exercise 7, 8 and 9 public clue records.
        (3, (), (0,1,2,3,4,5,6), (), (), 10),
        (3, (), (0,1,2,3,4,5,6,7), (), (), 10),
        (3, (), (0,1,2,3,4,5,6,7,8), (), (), 10),
    ]
    result = []
    for n, truth, opened, mines, safe, fuel in data:
        assert not set(opened) & set(truth)
        assert set(mines) <= set(truth)
        assert not set(safe) & set(truth)
        result.append((n, public_from_truth(n, truth, opened), mines,
                       tuple(sorted(set(safe) | set(opened))), fuel))
    # Public contract failures and insufficient fuel.
    base = ((1,1),(2,0),(4,1),(5,0))
    result.extend([
        (3, base, (), (1,2,4), 10),          # Unrevealed digit cell missing
        (3, base[:3]+(base[1],), (), (1,2,4,5), 10), # duplicate
        (3, base[:3]+((9,0),), (), (1,2,4,9), 10),  # outside board
        (3, base[:3]+((5,8),), (), (1,2,4,5), 10),  # impossible digit
        (3, base, (1,), (1,2,4,5), 10),       # mine overlaps revealed
        (3, base, (), (1,2,4,5), 0),         # no sweeps
        # Structural validation is necessary even with no public clues.
        (3, (), (0,), (0,), 1),              # overlap
        (3, (), (9,), (), 1),               # out-of-board mine
        (3, (), (), (9,), 1),               # out-of-board safe
        (3, (), (0,0), (), 1),             # repeated mine
        (3, (), (), (1,1), 1),             # repeated safe
        (3, (), (2,1), (), 1),             # unsorted mines
        (3, (), (), (2,1), 1),             # unsorted safe
        (3, (), (0,), (1,), 1),             # valid empty-clue evidence
        (2, (), (0,), (1,), 5),             # valid N=2 evidence
    ])
    return result


def literal(items):
    return "[" + ", ".join(map(str, items)) + "]" if items else "Nil{}"


def clue_literal(public):
    return "[" + ", ".join(f"Many.Clue{{{i}, {v}}}" for i,v in public) + "]" if public else "Nil{}"


def source(cases):
    lines = [
        "import Base",
        "import ./nxn_public_many_fixpoint.bend as Many",
        "import ./nxn_public_three_fixpoint.bend as Fix",
        "import ./nxn_public_local.bend as Rule", "",
        "def count(items: List<&2, U32>) -> U32:",
        "  match items:", "    case Nil{}:", "      0",
        "    case item <> rest:", "      (1 + count(rest) : U32)", "",
        "def subset(items: List<&2, U32>, +got: List<&2, U32>) -> Bool:",
        "  match items:", "    case Nil{}:", "      True{}",
        "    case item <> rest:",
        "      Bool.and(Rule.contains(got, item), subset(rest, got))", "",
        "def bit(ok: Bool) -> U32:", "  match ok:",
        "    case True{}:", "      1", "    case False{}:", "      0", "",
        "def valid(+expected_mines: List<&2, U32>, +expected_safe: List<&2, U32>,",
        "          result: Fix.Propagation) -> U32:",
        "  match result:", "    case Fix.Closure{+mines, +safe, changed}:",
        "      bit(Bool.and(U32.is_eq(count(mines), count(expected_mines)),",
        "          Bool.and(U32.is_eq(count(safe), count(expected_safe)),",
        "          Bool.and(subset(expected_mines, mines), subset(expected_safe, safe)))))",
        "    case Fix.Inconsistent{}:", "      0",
        "    case Fix.Limit{}:", "      0", "",
        "def rejected(result: Fix.Propagation) -> U32:",
        "  match result:", "    case Fix.Inconsistent{}:", "      1",
        "    case Fix.Limit{}:", "      0",
        "    case Fix.Closure{mines, safe, changed}:", "      0", "",
        "def limited(result: Fix.Propagation) -> U32:",
        "  match result:", "    case Fix.Limit{}:", "      1",
        "    case Fix.Inconsistent{}:", "      0",
        "    case Fix.Closure{mines, safe, changed}:", "      0", "",
    ]
    for i, (n, public, mines, safe, fuel) in enumerate(cases):
        expected = model(n, public, mines, safe, fuel)
        call = (f"Many.infer_many({n}, {clue_literal(public)}, "
                f"{fuel}n, {literal(mines)}, {literal(safe)})")
        lines.append(f"def case_{i}() -> U32:")
        if expected is None:
            lines.append(f"  rejected({call})")
        elif expected == "Limit":
            lines.append(f"  limited({call})")
        else:
            lines.append(f"  valid({literal(expected[0])}, {literal(expected[1])}, {call})")
        lines.append("")
    lines.extend(["def main() -> U32:",
                  "  (" + " + ".join(f"case_{i}()" for i in range(len(cases))) + " : U32)", ""])
    return "\n".join(lines)


def main():
    cases = fixtures()
    assert len(cases) == 28, len(cases)
    assert model(*cases[0]) == ((), (1,2,4,5,7,8))
    assert model(*cases[1]) == ((5,7), (0,1,2,3,4,6))
    assert model(*cases[9]) == "Limit"
    assert model(*cases[10]) == ((), tuple(range(9)))
    assert model(*cases[11]) == ((), tuple(range(9)))
    assert model(*cases[12]) == ((), tuple(range(9)))
    assert model(*cases[18]) == "Limit"
    assert model(*cases[-2]) == ((0,), (1,))
    assert model(*cases[-1]) == ((0,), (1,))
    print(f"PASS {len(cases)} Python many-clue fixture expectations", flush=True)
    if sys.argv[1:] == ["--model-only"]:
        return
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in FILES:
            (folder / name).write_bytes((GAME / name).read_bytes())
        program = folder / "check_many_fixpoint.bend"
        program.write_text(source(cases), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            p = subprocess.run(args, cwd=folder, capture_output=True, text=True,
                               timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{args}: {p.stdout}\n{p.stderr}")
            if len(args) == 2 and p.stdout.strip().splitlines()[-1] != str(len(cases)):
                raise AssertionError(f"expected {len(cases)} passing checks: {p.stdout}")
        sample = GAME / "nxn_public_many_fixpoint.bend"
        p = subprocess.run(("bend", str(sample)), cwd=GAME,
                           capture_output=True, text=True, timeout=360,
                           env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if p.returncode or p.stdout.strip().splitlines()[-1] != "6":
            raise AssertionError(f"many-clue sample: {p.stdout}\n{p.stderr}")
    print(f"PASS {len(cases)} Bend many-clue fixed-point checks")


if __name__ == "__main__":
    main()
