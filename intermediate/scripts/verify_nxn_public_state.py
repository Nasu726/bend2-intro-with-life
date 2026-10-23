#!/usr/bin/env python3
"""Finite Bend-vs-Python public clue-state gate; NOT a game/solver proof.

The oracle supplies public deltas from a separately audited safe replay.
Bend is responsible for retaining only opened cells and their clues.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
sys.path.insert(0, str(ROOT / "solutions"))
from nxn_replay_vectors import replay_vectors

MINES = frozenset({4, 29, 34, 36, 37, 49, 50, 56, 72, 77})
CLICKS = (0, 14, 5, 6, 24, 35, 38, 39, 46, 47, 48, 57, 67)
BOUNDARY = (0, 1, 4, 14, 29, 31, 32, 34, 36, 37, 49, 50, 56,
            63, 64, 72, 77, 88, 89, 98, 99)


def cases():
    """Each case: function name, initial expression, updates, expected reads."""
    frames = replay_vectors(10, MINES, CLICKS)
    result = []
    for step, frame in enumerate(frames):
        selected = sorted(set(BOUNDARY) |
                          {i for i, _ in frame.newly_opened[:2]} |
                          {i for i, _ in frame.newly_opened[-2:]})
        reads = [(i, dict(frame.opened).get(i, 9)) for i in selected]
        result.append((f"frame_{step}",
                       "Public.new(10)" if step == 0 else f"frame_{step-1}()",
                       frame.newly_opened, reads))

    for n in (2, 3, 4, 10, 17, 100):
        # A duplicate reveal, invalid clue and out-of-range indices are no-ops.
        actions = [(0, 8), (0, 1), (n*n, 3), (4294967295, 2),
                   (n*n-1, 9), (31, 3), (32, 4), (n*n-1, 5)]
        expected = {0: 8, n*n-1: 5}
        if 31 < n*n and 31 not in expected:
            expected[31] = 3
        if 32 < n*n and 32 not in expected:
            expected[32] = 4
        reads = [(i, expected.get(i, 9))
                 for i in sorted({0, 1, 31, 32, n*n-1, n*n, 4294967295})]
        result.append((f"boundary_{n}", f"Public.new({n})", actions, reads))
    return result


def program(test_cases):
    """Every expected public cell value is checked by Bend's main()."""
    parts = [
        "import Base",
        "import ./nxn_geometry.bend as Geo",
        "import ./nxn_mine_words.bend as Bits",
        "import ./nxn_public_state.bend as Public",
        "",
        "def compare_read(pair: Public.PublicState & U32, +want: U32, +total: U32) -> Public.PublicState & U32:",
        "  (board, got) = pair",
        "  (board, (total + Bool.to_u32(U32.is_eq(got, want)) : U32))",
        "",
        "def check_one(pair: Public.PublicState & U32, +i: U32, +want: U32) -> Public.PublicState & U32:",
        "  (board, total) = pair",
        "  compare_read(Public.read(board, i), want, total)",
        "",
        "def score(pair: Public.PublicState & U32) -> U32:",
        "  (unused, total) = pair",
        "  total",
        "",
    ]
    total = 0
    for name, initial, actions, reads in test_cases:
        parts += [f"def {name}() -> Public.PublicState:", f"  b0 = {initial}"]
        for j, (i, clue) in enumerate(actions, 1):
            parts.append(f"  b{j} = Public.reveal(b{j-1}, {i}, {clue})")
        parts += [f"  b{len(actions)}", ""]
        parts += [f"def check_{name}() -> U32:",
                  f"  p0 = check_one(({name}(), 0), {reads[0][0]}, {reads[0][1]})"]
        for j, (i, want) in enumerate(reads[1:], 1):
            parts.append(f"  p{j} = check_one(p{j-1}, {i}, {want})")
        parts += [f"  score(p{len(reads)-1})", ""]
        total += len(reads)
    parts += ["def main() -> U32:",
              "  (" + " + ".join(f"check_{name}()" for name, *_ in test_cases) + " : U32)", ""]
    return "\n".join(parts), total


def verify(runner=subprocess.run):
    source, count = program(cases())
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)
        for name in ("nxn_geometry.bend", "nxn_mine_words.bend", "nxn_public_state.bend"):
            shutil.copyfile(GAME / name, folder / name)
        entry = folder / "check_public.bend"
        entry.write_text(source, encoding="utf-8")
        for check_only in (True, False):
            command = ("bend", str(entry), "--check-only") if check_only else ("bend", str(entry))
            result = runner(command, capture_output=True, text=True, timeout=240,
                            cwd=folder, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if result.returncode:
                raise AssertionError(f"{command}: {result.stdout}\n{result.stderr}")
            if not check_only and result.stdout not in (str(count), str(count)+"\n", str(count)+"\r\n"):
                raise AssertionError(f"Bend public-state mismatch: {result.stdout!r}, expected {count}")
    return count


if __name__ == "__main__":
    print(f"PASS Bend public state: {verify()} finite public-clue reads")
