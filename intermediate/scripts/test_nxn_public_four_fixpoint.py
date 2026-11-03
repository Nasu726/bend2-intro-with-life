#!/usr/bin/env python3
"""Four-clue Bend fixed point vs independent simultaneous-round Python model.

This is a bounded four-clue *single-number* rule, not exact global inference.
Truth is used only to construct the fixture's revealed digits; never by Bend.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("nxn_geometry.bend", "nxn_neighbors.bend", "nxn_public_local.bend",
         "nxn_public_three_fixpoint.bend", "nxn_public_four_fixpoint.bend")


def neighbors(n, cell):
    return {j for j in range(n*n) if j != cell
            and abs(cell % n - j % n) <= 1
            and abs(cell // n - j // n) <= 1}


def public_clues(n, mines, opened):
    return tuple((cell, len(neighbors(n, cell) & set(mines))) for cell in opened)


def model(n, public, mines=(), safe=()):
    """Synchronous fixed point; independent of Bend's ordered updates."""
    if type(n) is not int or not 2 <= n <= 100 or len(public) != 4:
        return None
    shown = {cell for cell, _ in public}
    known_mines, known_safe = set(mines), set(safe) | shown
    if len(shown) != 4 or known_mines & known_safe:
        return None
    if any(type(cell) is not int or type(value) is not int or
           not 0 <= cell < n*n or not 0 <= value <= 8 for cell, value in public):
        return None
    if any(type(cell) is not int or not 0 <= cell < n*n
           for cell in (*mines, *safe)):
        return None
    for _ in range(33):
        add_mines, add_safe = set(), set()
        for cell, value in public:
            around = neighbors(n, cell)
            unknown = around - known_mines - known_safe
            remaining = value - len(around & known_mines)
            if not 0 <= remaining <= len(unknown):
                return None
            if remaining == 0:
                add_safe |= unknown
            if remaining == len(unknown):
                add_mines |= unknown
        if add_mines & (known_safe | add_safe) or add_safe & known_mines:
            return None
        add_mines -= known_mines
        add_safe -= known_safe
        if not add_mines and not add_safe:
            return tuple(sorted(known_mines)), tuple(sorted(known_safe))
        known_mines |= add_mines
        known_safe |= add_safe
    raise AssertionError("four-clue closure did not converge within 33 rounds")


def fixtures():
    valid = (
        (3, (0,), (1, 2, 4, 5), (), ()),
        (3, (5, 7), (0, 2, 3, 6), (), ()),
        (3, (), (0, 1, 2, 6), (), ()),
        (4, (3, 15), (0, 1, 4, 5), (), ()),
        (5, (12, 24), (0, 1, 5, 6), (), (2, 3)),
        (10, (99,), (0, 1, 10, 11), (), ()),
        (3, (0,), (1, 2, 4, 5), (0,), ()),
    )
    examples = []
    for n, truth, opened, known_mines, safe in valid:
        assert set(known_mines) <= set(truth)
        assert not set(safe) & set(truth)
        examples.append((n, public_clues(n, truth, opened), known_mines, safe))
    # Invalid clue index, missing revealed cell in input safe list,
    # duplicate public clue, impossible local digit, and a false mine.
    examples += [
        (3, ((1, 1), (2, 0), (4, 1), (9, 0)), (), ()),
        (3, ((1, 1), (2, 0), (4, 1), (5, 0)), (), (), "missing"),
        (3, ((1, 1), (2, 0), (4, 1), (4, 1)), (), ()),
        (3, ((1, 1), (2, 8), (4, 1), (5, 0)), (), ()),
        (3, ((1, 1), (2, 0), (4, 1), (5, 0)), (8,), ()),
    ]
    return examples


def literal(items):
    return "[" + ", ".join(map(str, items)) + "]" if items else "Nil{}"


def source(cases):
    parts = [
        "import Base", "import ./nxn_public_four_fixpoint.bend as Four",
        "import ./nxn_public_three_fixpoint.bend as Fix",
        "import ./nxn_public_local.bend as Rule", "",
        "def count(xs: List<&2, U32>) -> U32:",
        "  match xs:", "    case Nil{}:", "      0",
        "    case x <> rest:", "      (1 + count(rest) : U32)", "",
        "def subset(xs: List<&2, U32>, +ys: List<&2, U32>) -> Bool:",
        "  match xs:", "    case Nil{}:", "      True{}",
        "    case x <> rest:",
        "      Bool.and(Rule.contains(ys, x), subset(rest, ys))", "",
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
    ]
    for i, item in enumerate(cases):
        n, shown, mines, safe = item[:4]
        safe_list = tuple(sorted(set(safe) | {cell for cell, _ in shown}))
        if len(item) == 5 and item[4] == "missing":
            safe_list = tuple(sorted(set(safe) | {cell for cell, _ in shown[:-1]}))
        expected = model(n, shown, mines, safe)
        if len(item) == 5 and item[4] == "missing":
            expected = None
        argv = ", ".join(map(str, (n, *sum(([c, v] for c, v in shown), []))))
        call = f"Four.infer_four({argv}, {literal(mines)}, {literal(safe_list)})"
        parts += [f"def case_{i}() -> U32:"]
        if expected is None:
            parts += [f"  rejected({call})", ""]
        else:
            parts += [f"  valid({literal(expected[0])}, {literal(expected[1])}, {call})", ""]
    parts += ["def main() -> U32:",
              "  (" + " + ".join(f"case_{i}()" for i in range(len(cases))) + " : U32)", ""]
    return "\n".join(parts)


def main():
    cases = fixtures()
    assert len(cases) == 12
    first = model(*cases[0])
    assert first == ((), (1, 2, 4, 5, 7, 8)), first
    assert model(3, cases[0][1][:3]) is None  # Four digits are required.
    assert model(*cases[6]) == ((0,), (1, 2, 3, 4, 5, 6, 7, 8))
    print(f"PASS {len(cases)} Python four-clue expectations", flush=True)
    if sys.argv[1:] == ["--model-only"]:
        return
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in FILES:
            (folder / name).write_bytes((GAME / name).read_bytes())
        program = folder / "check_four_fixpoint.bend"
        program.write_text(source(cases), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            p = subprocess.run(args, cwd=folder, capture_output=True, text=True,
                               timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{args}: {p.stdout}\n{p.stderr}")
            if len(args) == 2 and p.stdout.strip().splitlines()[-1] != str(len(cases)):
                raise AssertionError(f"expected {len(cases)} passing checks: {p.stdout}")
        sample = GAME / "nxn_public_four_fixpoint.bend"
        p = subprocess.run(("bend", str(sample)), cwd=GAME,
                           capture_output=True, text=True, timeout=360,
                           env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if p.returncode or p.stdout.strip().splitlines()[-1] != "6":
            raise AssertionError(f"four clue sample: {p.stdout}\n{p.stderr}")
    print(f"PASS {len(cases)} Bend four-clue fixed-point checks")


if __name__ == "__main__":
    main()
