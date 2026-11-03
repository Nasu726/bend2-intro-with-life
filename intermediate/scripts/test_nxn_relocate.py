#!/usr/bin/env python3
"""Independent finite oracle for first-click N x N mine relocation.

Checks Bend typechecking and execution, not GUI or a complete game. The
reference uses Python sets, not Bend's packed U32 word representation.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("nxn_geometry.bend", "nxn_mine_words.bend", "nxn_relocate.bend")


def oracle(n, mines, clicked):
    mines = set(mines)
    if not 0 <= clicked < n*n:
        return False, mines
    if clicked not in mines:
        return True, mines
    free = next((i for i in range(n*n) if i not in mines), None)
    if free is None:
        return False, mines
    mines.remove(clicked)
    mines.add(free)
    return True, mines


def cases():
    boards = (
        (2, (), 0),
        (2, (0,), 0),
        (2, (0, 1, 2), 0),
        (2, (0, 1, 2, 3), 0),
        (2, (1,), 0),
        (3, (0, 1, 2, 3, 4, 5, 6, 7), 0),
        (3, (8,), 8),
        (10, (0, 99), 0),
        (10, (0, 1, 2, 99), 0),
        (10, (9, 10), 9),
        (10, (99,), 0),
        (10, (99,), 99),
        (10, (0, 99), 100),
        (10, (0, 99), 127),
        (100, (0, 9999), 0),
        (100, (0, 1, 31, 32, 9999), 0),
        (100, (9999,), 9999),
        (100, (0, 9999), 10000),
        (100, (0, 9999), 16383),
    )
    result = []
    for n, mines, clicked in boards:
        ok, after = oracle(n, mines, clicked)
        # Probe the click, first free cells, a word boundary, and the last cell.
        probes = sorted({0, 1, 2, 3, 31, 32, clicked, n*n-1} &
                        set(range(n*n)))
        for probe in probes:
            result.append((n, mines, clicked, probe,
                           (0 if ok else 2) + (probe in after)))
    return result


def source(all_cases):
    lines = [
        "import Base",
        "import ./nxn_mine_words.bend as Words",
        "import ./nxn_relocate.bend as Relocate",
        "",
        "def one_if_true(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0",
        "",
        "def one_if_equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))",
        "",
    ]
    for k, (n, mines, clicked, probe, want) in enumerate(all_cases):
        lines.append(f"def case_{k}() -> U32:")
        lines.append(f"  board = Words.new({n})")
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append(
            f"  one_if_equal(Relocate.inspect(Relocate.relocate(board, {clicked}), {probe}), {want})"
        )
        lines.append("")
    lines.append("def main() -> U32:")
    lines.append("  (" + " + ".join(f"case_{k}()" for k in range(len(all_cases))) + " : U32)")
    return "\n".join(lines) + "\n"


def main():
    all_cases = cases()
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        path = directory / "check_nxn_relocate.bend"
        path.write_text(source(all_cases), encoding="utf-8")
        for args in (("bend", str(path), "--check-only"), ("bend", str(path))):
            print(f"CHECK N x N first-click relocation: {len(all_cases)} cases / {args[-1]}", flush=True)
            proc = subprocess.run(args, cwd=directory, capture_output=True,
                                  text=True, timeout=360,
                                  env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(all_cases)):
                raise AssertionError(
                    f"Expected {len(all_cases)} independent matches, got {proc.stdout}"
                )
    print(f"PASS {len(all_cases)} independent Bend relocation checks")


if __name__ == "__main__":
    main()
