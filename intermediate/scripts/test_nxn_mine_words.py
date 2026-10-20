#!/usr/bin/env python3
"""Finite Bend-vs-Python differential tests for N x N mine-word storage.

Not a game-engine proof. The Python oracle is separately tested in
test_nxn_word_storage.py; no GUI or no-guess solver is exercised.
"""
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "minesweeper" / "nxn_mine_words.bend"
GEOMETRY = ROOT / "minesweeper" / "nxn_geometry.bend"
sys.path.insert(0, str(ROOT / "solutions"))
import nxn_word_storage as oracle


def cases():
    checks = []
    def add(n, actions, read):
        state = f"Mines.new({n})"
        words = oracle.pack(n, ())
        for i, enabled in actions:
            state = f"Mines.set_checked({state}, {i}, {'True{}' if enabled else 'False{}'})"
            if i < n*n:
                words = oracle.set_cell(n, words, i, enabled)
        actual = f"Mines.read_bit(Mines.has({state}, {read}))"
        expected = int(oracle.has(n, words, read))
        checks.append(f"bit(U32.is_eq({actual}, {expected}))")

    for n in (2, 3, 4, 10, 17, 100):
        for i in sorted({0, 1, n*n-1, 31, 32, 63, 64, 99, n*n, n*n+27, 4294967295}):
            add(n, [(i, True)], i)
            add(n, [(i, True)], 0)
        rng = random.Random(20261020 + n)
        for _ in range(12):
            actions = [(rng.randrange(n*n), bool(rng.randrange(2))) for _ in range(3)]
            add(n, actions, rng.randrange(n*n))
    return checks


def program(checks):
    groups = []
    for i in range(0, len(checks), 4):
        groups.append(f"def group_{i}() -> U32:\n  ("
                      + " + ".join(checks[i:i+4]) + " : U32)")
    return ("import Base\nimport ./nxn_geometry.bend as Geo\n"
            "import ./nxn_mine_words.bend as Mines\n"
            "def bit(b: Bool) -> U32:\n  match b:\n"
            "    case True{}:\n      1\n    case False{}:\n      0\n\n"
            + "\n\n".join(groups)
            + "\n\ndef main() -> U32:\n  ("
            + " + ".join(f"group_{i}()" for i in range(0, len(checks), 4))
            + " : U32)\n")


def main():
    checks = cases()
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)
        shutil.copyfile(MODULE, folder / MODULE.name)
        shutil.copyfile(GEOMETRY, folder / GEOMETRY.name)
        entry = folder / "check_mines.bend"
        entry.write_text(program(checks), encoding="utf8")
        for args in (("bend", str(entry), "--check-only"), ("bend", str(entry))):
            result = subprocess.run(args, capture_output=True, text=True,
                                    timeout=240, cwd=folder,
                                    env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if result.returncode:
                raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
            if len(args) == 2:
                found = result.stdout.strip().splitlines()[-1]
                if found != str(len(checks)):
                    raise AssertionError(f"mine words: {found} != {len(checks)}")
    print(f"PASS Bend N x N mine words: {len(checks)} independent finite checks")


if __name__ == "__main__":
    main()
