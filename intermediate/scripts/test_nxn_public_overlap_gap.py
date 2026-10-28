#!/usr/bin/env python3
"""All real 3x3 two-clue states: find nonnested overlap deductions that
single-clue fixed-point and subset-only reasoning cannot make.

The independent truth masks are NEVER passed to Bend. Only public clues and
their unknown-neighbor sets are used in generated Bend fixtures.
"""
from collections import Counter
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from test_nxn_public_pair_gap import N, NEIGHBORS, public_states
from test_nxn_public_many_fixpoint import model as single_model
from test_nxn_public_overlap import oracle as overlap_oracle, source as overlap_source

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def audit():
    states = public_states()
    assert len(states) == 560, len(states)
    witnessed = Counter()
    cases = []
    for public, truth_masks in sorted(states.items()):
        opened = {index for index, _ in public}
        (i, ra), (j, rb) = public
        a = tuple(sorted(NEIGHBORS[i] - opened))
        b = tuple(sorted(NEIGHBORS[j] - opened))
        tag, safe, mines = overlap_oracle(a, b, ra, rb)
        # Every public state came from at least one real hidden board.
        assert tag == 1, public
        assert all(not (mask & (1 << k))
                   for mask in truth_masks for k in safe), public
        assert all(mask & (1 << k)
                   for mask in truth_masks for k in mines), public
        # A nested pair is already covered by the subset lesson.
        if set(a) <= set(b) or set(b) <= set(a):
            continue
        if single_model(N, public, (), tuple(sorted(opened))) != ((), tuple(sorted(opened))):
            continue
        if not safe and not mines:
            continue
        witnessed[(len(safe), len(mines))] += 1
        cases.append((a, b, ra, rb))

    assert len(cases) == 40, (len(cases), witnessed)
    assert witnessed == Counter({(1, 1): 8, (1, 3): 8,
                                 (3, 1): 8, (2, 2): 16}), witnessed
    public = ((0, 1), (2, 2))
    assert single_model(N, public, (), (0, 2)) == ((), (0, 2))
    assert overlap_oracle((1, 3, 4), (1, 4, 5), 1, 2) == (1, (3,), (5,))
    assert len(states[public]) == 16
    assert ((1, 3, 4), (1, 4, 5), 1, 2) in cases
    return cases


def main():
    cases = audit()
    print("PASS 560 public states; 40 nonnested overlap-only witnesses", flush=True)
    if sys.argv[1:] == ["--model-only"]:
        return
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in ("nxn_public_subset.bend", "nxn_public_overlap.bend"):
            (folder / name).write_bytes((GAME / name).read_bytes())
        program = folder / "check_public_overlap_gap.bend"
        program.write_text(overlap_source(cases), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            p = subprocess.run(args, cwd=folder, capture_output=True,
                               text=True, timeout=360,
                               env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{args}: {p.stdout}\\n{p.stderr}")
            if len(args) == 2 and p.stdout.strip().splitlines()[-1] != str(len(cases)):
                raise AssertionError(f"Expected {len(cases)} cases: {p.stdout}")
        sample = GAME / "nxn_public_overlap_gap.bend"
        for args in (("bend", str(sample), "--check-only"),
                     ("bend", str(sample))):
            p = subprocess.run(args, cwd=GAME, capture_output=True,
                               text=True, timeout=360,
                               env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{args}: {p.stdout}\\n{p.stderr}")
            if len(args) == 2 and p.stdout.strip().splitlines()[-1] != "211":
                raise AssertionError(f"Expected 211: {p.stdout}")
    print("PASS 40 public-derived Bend overlap cases and 211 example")


if __name__ == "__main__":
    main()
