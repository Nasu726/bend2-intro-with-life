#!/usr/bin/env python3
"""N x N quarter-density construction: independently audit public-only clicks."""
from functools import lru_cache
from itertools import product
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
MODULE = GAME / "nxn_noguess_density.bend"

@lru_cache(maxsize=None)
def neighbors(n, i):
    x, y = i%n, i//n
    return tuple(v*n+u for v in range(max(0,y-1),min(n,y+2))
                 for u in range(max(0,x-1),min(n,x+2)) if (u,v)!=(x,y))

def construction(n, m, first):
    if (type(n) is not int or type(m) is not int or type(first) is not int
            or not 10<=n<=100 or not 0<=m<=n*n//4 or not 0<=first<n*n):
        return None
    right = first%n < n//2
    q, r = divmod(m,n)
    mines = set()
    for k in range(q):
        col = n-1-k if right else k
        mines.update(y*n+col for y in range(n))
    if r:
        col = n-1-q if right else q
        mines.update(y*n+col for y in range(n-r,n))
    assert len(mines)==m and first not in mines
    assert not mines.intersection(neighbors(n,first))
    return frozenset(mines)

def reveal(n, truth, opened, cell):
    """The truth crosses only the game simulation boundary."""
    todo = [cell]
    while todo:
        i = todo.pop()
        if i in opened:
            continue
        if i in truth:
            raise AssertionError("mined square opened")
        adj = neighbors(n,i)
        clue = sum(k in truth for k in adj)
        opened[i] = clue
        if clue == 0:
            todo.extend(k for k in adj if k not in opened)

def public_deduce(n, opened, known_mines):
    """Uses publicly revealed clues ONLY. No secret mines and no flags."""
    safe, mines = set(), set()
    for i, value in opened.items():
        around = neighbors(n,i)
        remaining = value - sum(k in known_mines for k in around)
        unknown = [k for k in around if k not in opened and k not in known_mines]
        if not 0<=remaining<=len(unknown):
            raise AssertionError("inconsistent public digit")
        if remaining==0:
            safe.update(unknown)
        elif remaining==len(unknown):
            mines.update(unknown)
    if mines & safe:
        raise AssertionError("contradictory inferences")
    return safe, mines

def replay(n,m,first):
    truth = construction(n,m,first)
    if truth is None:
        raise ValueError("invalid generator input")
    opened, proved = {}, set()
    reveal(n,truth,opened,first)
    clicks = [first]
    while len(opened) != n*n-m:
        safe, mines = public_deduce(n,opened,proved)
        safe.difference_update(opened)
        mines.difference_update(proved)
        if not safe and not mines:
            raise AssertionError(("guess needed",n,m,first,len(opened)))
        # This independent truth comparison is OUTSIDE the public solver.
        assert not (safe & truth) and not (mines - truth)
        proved.update(mines)
        for cell in sorted(safe):
            if cell not in opened:
                reveal(n,truth,opened,cell)
                clicks.append(cell)
    return clicks

HARNESS = """import Base
import ./nxn_noguess_density.bend as Gen
import ./nxn_mine_words.bend as Words

def bit(result: Gen.Construction, i: U32) -> U32:
  match result:
    case Gen.Candidate{board, first, last}:
      Words.read_bit(Words.has(board, i))
    case Gen.Unsupported{}:
      9

def invalid(result: Gen.Construction) -> U32:
  match result:
    case Gen.Candidate{board, first, last}:
      0
    case Gen.Unsupported{}:
      1

def main() -> U32:
  (bit(Gen.generate(10,25,0), 8) + bit(Gen.generate(10,25,0), 98) +
   bit(Gen.generate(10,25,0), 7) + bit(Gen.generate(10,25,55), 0) +
   bit(Gen.generate(10,25,55), 90) + bit(Gen.generate(10,25,55), 2) +
   bit(Gen.generate(100,2500,0), 75) + bit(Gen.generate(100,2500,0), 74) +
   invalid(Gen.generate(9,1,0)) + invalid(Gen.generate(10,26,0)) +
   invalid(Gen.generate(10,1,100)) : U32)
"""

def run_bend(path, expected):
    env = dict(os.environ,BEND_NO_TELEMETRY="1")
    for args in (("bend",str(path),"--check-only"),("bend",str(path))):
        p = subprocess.run(args,cwd=path.parent,env=env,capture_output=True,
                           text=True,timeout=700)
        if p.returncode:
            raise AssertionError(f"{args}: {p.stdout}\n{p.stderr}")
        if len(args)==2 and p.stdout.strip().splitlines()[-1]!=str(expected):
            raise AssertionError(f"{args}: expected {expected}, got {p.stdout!r}")

def main():
    count = 0
    for n in range(10,26):
        for m in range(n*n//4+1):
            for first in {0,n-1,n*(n-1),n*n-1,(n//2)*n+n//2}:
                replay(n,m,first)
                count += 1
    for n in (26,27,30,36,48,50,75,99,100):
        ms = {0,1,2,n-1,n,n+1,2*n-1,2*n,2*n+1,
              n*n//8,n*n//4-1,n*n//4}
        fs = {0,n-1,n*(n-1),n*n-1,(n//2)*n+n//2}
        for m,first in product(sorted(k for k in ms if k<=n*n//4),sorted(fs)):
            replay(n,m,first)
            count += 1
    assert count==7160, count
    for args in ((9,1,0),(10,26,0),(10,1,100),(100,2501,0),
                 (10,-1,0),(101,1,0),(10,2,-1),(True,1,0)):
        assert construction(*args) is None
    try:
        public_deduce(10,{80:9},set())
    except AssertionError:
        pass
    else:
        raise AssertionError("inconsistent public clue accepted")
    print(f"PASS {count} public-only quarter-density N x N traces",flush=True)
    if sys.argv[1:]==["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_noguess_density.py [--static-only]")
    src=MODULE.read_text(encoding="utf-8")
    assert "def fill_columns(" in src and "def generate(" in src
    run_bend(MODULE,112)
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp)
        for file in GAME.glob("*.bend"):
            (folder/file.name).write_bytes(file.read_bytes())
        program=folder/"check_nxn_density.bend"
        program.write_text(HARNESS,encoding="utf-8")
        run_bend(program,8)
    print("PASS Bend quarter-density construction typecheck and finite probes")

if __name__=="__main__":
    main()
