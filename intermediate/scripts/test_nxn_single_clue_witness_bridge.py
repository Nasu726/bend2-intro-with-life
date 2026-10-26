#!/usr/bin/env python3
"""Cross-check Python witness steps against Bend's public single-clue rule.

Finite conditional test, NOT a Bend fixed-point solver. Hidden fixture mines
are used ONLY to calculate public clue numbers, never passed to inference.
Other opened clue cells must be passed as certified-safe to the Bend kernel.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_single_clue_certificate import certify

FILES = ("nxn_geometry.bend", "nxn_neighbors.bend", "nxn_public_local.bend")


def neighbors(n, cell):
    return {r*n+c for r in range(max(0, cell//n-1), min(n, cell//n+2))
            for c in range(max(0, cell%n-1), min(n, cell%n+2))
            if r*n+c != cell}


def fixtures():
    # (size, true mines, opened cells, independently certified mines, safe)
    return (
        (3, (5, 7), (0, 2, 6), (), ()),
        (3, (), (0, 1), (), ()),  # Adjacent revealed clues are NOT unknown.
        (4, (3, 15), (0, 1, 4, 5, 10), (), ()),
        (5, (12, 24), (0, 1, 5, 6, 18), (), (2, 3)),
        (2, (3,), (0,), (), (1, 2)),
        (10, (99,), (0, 1, 10), (), ()),
    )


def proof_cases():
    """Yield (n, clue cell, clue number, known mines, known safe, step)."""
    for n, truth, opened, initial_mines, initial_safe in fixtures():
        truth, opened = set(truth), set(opened)
        assert not truth & opened
        assert set(initial_mines) <= truth
        assert not (set(initial_safe) & truth)
        public = tuple((cell, len(neighbors(n, cell) & truth))
                       for cell in sorted(opened))
        _, _, proof = certify(n, public, initial_mines, initial_safe)
        mines, safe = set(initial_mines), set(initial_safe)
        for step in proof:
            assert step.clue in opened
            # Bend's single-clue kernel does not receive the opened list.
            # Encode all opened cells as safe so they cannot be re-deduced.
            yield (n, step.clue, dict(public)[step.clue],
                   tuple(sorted(mines)), tuple(sorted(safe | opened)), step)
            mines.update(step.mines)
            safe.update(step.safe)


def literal(items):
    return "[" + ", ".join(map(str, items)) + "]" if items else "Nil{}"


def bend_source(cases):
    lines = [
        "import Base", "import ./nxn_public_local.bend as Rule", "",
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
        "def bit(ok: Bool) -> U32:",
        "  match ok:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def check(tag: U32, expected: List<U32>, result: Rule.Decision) -> U32:",
        "  match result:",
        "    case Rule.Safe{indices}:",
        "      bit(Bool.and(U32.is_eq(tag, 1), same(indices, expected)))",
        "    case Rule.Mines{indices}:",
        "      bit(Bool.and(U32.is_eq(tag, 2), same(indices, expected)))",
        "    case Rule.NoMove{}:", "      0",
        "    case Rule.Inconsistent{}:", "      0", "",
    ]
    for i, (n, cell, clue, mines, safe, step) in enumerate(cases):
        tag = 2 if step.mines else 1
        expected = step.mines if step.mines else step.safe
        assert expected and not (step.mines and step.safe)
        lines += [f"def case_{i}() -> U32:",
                  f"  check({tag}, {literal(expected)}, "
                  f"Rule.infer({n}, {cell}, {clue}, {literal(mines)}, {literal(safe)}))", ""]
    for start in range(0, len(cases), 8):
        lines += [f"def group_{start}() -> U32:",
                  "  (" + " + ".join(f"case_{j}()" for j in range(start, min(start+8, len(cases)))) + " : U32)", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"group_{i}()" for i in range(0, len(cases), 8)) + " : U32)", ""]
    return "\n".join(lines)


def main():
    cases = tuple(proof_cases())
    assert len(cases) >= 6, "fixtures must exercise actual propagation"
    assert any(n == 3 and cell == 0 and 1 in safe
               for n, cell, _, _, safe, _ in cases), "adjacent public-clue exclusion is not covered"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        for name in FILES:
            (path / name).write_bytes((GAME / name).read_bytes())
        program = path / "check_witness_steps.bend"
        program.write_text(bend_source(cases), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            proc = subprocess.run(args, cwd=path, capture_output=True, text=True,
                                  timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(cases)):
                raise AssertionError(f"expected {len(cases)} exact proof steps: {proc.stdout}")
    print(f"PASS {len(cases)} Python witness steps reproduced by Bend local inference")


if __name__ == "__main__":
    main()
