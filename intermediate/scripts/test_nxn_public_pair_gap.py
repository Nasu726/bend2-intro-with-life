#!/usr/bin/env python3
"""Public 3x3 two-clue witnesses where subset inference improves on the
single-clue fixed point. Truth layouts are used only by the independent oracle.
"""
from collections import Counter, defaultdict
from itertools import combinations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
from test_nxn_public_subset import oracle as subset_oracle, source as subset_source
from test_nxn_public_many_fixpoint import model as single_model

N = 3
CELLS = range(N*N)
NEIGHBORS = {
    i: {j for j in CELLS if j != i and abs(i % N-j % N) <= 1
        and abs(i // N-j // N) <= 1}
    for i in CELLS
}


def public_states():
    states = defaultdict(set)
    for truth in range(1 << (N*N)):
        mines = {i for i in CELLS if truth & (1 << i)}
        for opened in combinations(sorted(set(CELLS)-mines), 2):
            public = tuple((i, len(NEIGHBORS[i] & mines)) for i in opened)
            states[public].add(truth)
    return states


def audit():
    states = public_states()
    assert len(states) == 560, len(states)
    witnessed = Counter()
    cases = []
    for public, truth_masks in sorted(states.items()):
        opened = tuple(i for i, _ in public)
        single = single_model(N, public, (), opened)
        assert isinstance(single, tuple), public
        if single != ((), opened):
            continue  # the single-clue rule already makes a decision
        (i, ra), (j, rb) = public
        a = tuple(sorted(NEIGHBORS[i]-set(opened)))
        b = tuple(sorted(NEIGHBORS[j]-set(opened)))
        if a == b or not (set(a) <= set(b) or set(b) <= set(a)):
            continue
        tag, indices = subset_oracle(a, b, ra, rb)
        if tag not in (1, 2):
            continue
        assert indices, public
        if tag == 1:
            assert all(not (mask & (1 << k))
                       for mask in truth_masks for k in indices), public
            witnessed["safe"] += 1
        else:
            assert all(mask & (1 << k)
                       for mask in truth_masks for k in indices), public
            witnessed["mine"] += 1
        cases.append((a, b, ra, rb))
    assert witnessed == Counter({"safe": 24, "mine": 24}), witnessed
    assert len(cases) == 48

    for public, expected_tag, expected_cells in (
        (((1, 1), (4, 1)), 1, (6, 7, 8)),
        (((4, 4), (7, 1)), 2, (0, 1, 2)),
    ):
        opened = tuple(i for i, _ in public)
        (i, ra), (j, rb) = public
        a = tuple(sorted(NEIGHBORS[i]-set(opened)))
        b = tuple(sorted(NEIGHBORS[j]-set(opened)))
        assert single_model(N, public, (), opened) == ((), opened)
        assert subset_oracle(a, b, ra, rb) == (expected_tag, expected_cells)
        assert (a, b, ra, rb) in cases
        assert len(states[public]) == 4
    return cases


def main():
    cases = audit()
    print("PASS 560 public states, 24 safe + 24 mine pairwise gap witnesses", flush=True)
    if sys.argv[1:] == ["--model-only"]:
        return
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        (folder / "nxn_public_subset.bend").write_bytes(
            (GAME / "nxn_public_subset.bend").read_bytes())
        program = folder / "check_public_pair_gap.bend"
        program.write_text(subset_source(cases), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            p = subprocess.run(args, cwd=folder, capture_output=True, text=True,
                               timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{args}: {p.stdout}\n{p.stderr}")
            if len(args) == 2 and p.stdout.strip().splitlines()[-1] != str(len(cases)):
                raise AssertionError(f"Expected {len(cases)} passing checks: {p.stdout}")
        sample = GAME / "nxn_public_pair_gap.bend"
        p = subprocess.run(("bend", str(sample)), cwd=GAME,
                           capture_output=True, text=True, timeout=360,
                           env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if p.returncode or p.stdout.strip().splitlines()[-1] != "203":
            raise AssertionError(f"Expected 203 from public pair sample: {p.stdout}\n{p.stderr}")
    print("PASS 48 public-derived Bend subset cases and 203 example")


if __name__ == "__main__":
    main()
