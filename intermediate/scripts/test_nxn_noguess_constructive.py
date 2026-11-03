#!/usr/bin/env python3
"""Constructive N x N no-guess family: public-only independent verification.

Truth is used to simulate clicks, never as input to infer_from_public.
A finite audit does not prove the general theorem; the chapter states the
inductive proof. Bend demonstration knows the layout and is not the solver.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def neighbors(n, cell):
    x, y = cell % n, cell // n
    return [v*n + u for v in range(max(0, y-1), min(n, y+2))
            for u in range(max(0, x-1), min(n, x+2)) if (u, v) != (x, y)]


def construction(n, first):
    if type(n) is not int or type(first) is not int or not 10 <= n <= 100 or not 0 <= first < n*n:
        return None
    edge = n-1 if first//n < n//2 else 0
    return edge, frozenset(edge*n+x for x in range(n-1)), edge*n+n-1


def observe(n, mines, first):
    opened = {}
    pending = [first]
    while pending:
        cell = pending.pop()
        if cell in opened:
            continue
        if cell in mines:
            raise AssertionError("opened a mine")
        value = sum(k in mines for k in neighbors(n, cell))
        opened[cell] = value
        if value == 0:
            pending.extend(neighbors(n, cell))
    return opened


def infer_from_public(n, edge, opened):
    """Deduce from revealed clues only; no truth or flags can enter."""
    known_safe = set(opened)
    known_mines = set()
    border = 1 if edge == 0 else n-2
    for column in range(n):
        cell = border*n+column
        if cell not in opened:
            raise AssertionError("border clue not visible")
        around = neighbors(n, cell)
        remaining = opened[cell] - sum(k in known_mines for k in around)
        unknown = set(around) - known_safe - known_mines
        if not 0 <= remaining <= len(unknown):
            raise AssertionError("contradictory public clue")
        if remaining == len(unknown):
            known_mines.update(unknown)
        elif remaining == 0:
            known_safe.update(unknown)
        elif unknown:
            raise AssertionError("would need a guess")
    return known_mines, known_safe


def check(n, first):
    edge, mines, last = construction(n, first)
    opened = observe(n, mines, first)
    assert len(opened) == n*n-n, (n, first, len(opened))
    assert len(mines) == n-1 and last not in opened and last not in mines
    certified_mines, certified_safe = infer_from_public(n, edge, opened)
    assert certified_mines == mines
    assert certified_safe == set(opened) | {last}
    assert len(certified_safe) == n*n-len(mines)


HARNESS = """import Base
import ./nxn_noguess_constructive.bend as NG
import ./nxn_mine_words.bend as Words

def bit(candidate: NG.Construction, index: U32) -> U32:
  match candidate:
    case NG.Candidate{board, first, last}:
      Words.read_bit(Words.has(board, index))
    case NG.Unsupported{}:
      9

def bad(candidate: NG.Construction) -> U32:
  match candidate:
    case NG.Candidate{board, first, last}:
      0
    case NG.Unsupported{}:
      1

def main() -> U32:
  (bit(NG.generate(10, 0), 90) + bit(NG.generate(10, 0), 98) +
   bit(NG.generate(10, 0), 99) + bit(NG.generate(10, 99), 0) +
   bit(NG.generate(10, 99), 8) + bit(NG.generate(10, 99), 9) +
   bit(NG.generate(100, 0), 9900) + bit(NG.generate(100, 0), 9998) +
   bit(NG.generate(100, 0), 9999) + bit(NG.generate(100, 9999), 0) +
   bit(NG.generate(100, 9999), 98) + bit(NG.generate(100, 9999), 99) +
   bad(NG.generate(9, 0)) + bad(NG.generate(101, 0)) +
   bad(NG.generate(10, 100)) : U32)
"""


def bend_run(path, expected):
    env = dict(os.environ, BEND_NO_TELEMETRY="1")
    for argv in (("bend", str(path), "--check-only"), ("bend", str(path))):
        p = subprocess.run(argv, cwd=path.parent, capture_output=True, text=True,
                           env=env, timeout=700)
        if p.returncode:
            raise AssertionError(f"{argv}: {p.stdout}\n{p.stderr}")
        if len(argv) == 2 and p.stdout.strip().splitlines()[-1] != str(expected):
            raise AssertionError(f"{argv}: expected {expected}, got {p.stdout!r}")


def main():
    count = 0
    for n in range(10, 101):
        cases = {0, n-1, n*(n-1), n*n-1, (n//2)*n+n//2,
                 2*n+3, (n-3)*n+1}
        for first in cases:
            check(n, first)
            count += 1
    assert count == 637
    for n, first in ((9, 0), (101, 0), (10, 100), (10, -1)):
        assert construction(n, first) is None
    edge, mines, last = construction(10, 0)
    bad = observe(10, mines, 0)
    bad[80] = 1  # The first border clue must be 2, not 1.
    try:
        infer_from_public(10, edge, bad)
    except AssertionError:
        pass
    else:
        raise AssertionError("ambiguous forged clue accepted")
    print(f"PASS {count} N=10..100 public-only construction checks", flush=True)
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_noguess_constructive.py [--static-only]")
    root = Path(__file__).resolve().parents[1] / "minesweeper"
    source = root / "nxn_noguess_constructive.bend"
    assert "def generate(" in source.read_text(encoding="utf-8")
    bend_run(source, 111)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        for file in root.glob("*.bend"):
            (target / file.name).write_bytes(file.read_bytes())
        harness = target / "check_constructive.bend"
        harness.write_text(HARNESS, encoding="utf-8")
        bend_run(harness, 11)
    print("PASS Bend N=10 two-click victory and N=10/100 construction boundaries")


if __name__ == "__main__":
    main()
