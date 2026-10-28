#!/usr/bin/env python3
"""Audit all 3x3 two-public-clue observations against independent layouts.

The complete 560-state audit is Python-only. The 40 public-derived,
non-nested improvement cases are separately typechecked and executed in Bend.
No hidden mine truth or player flags enter the Bend inference kernel.
"""
from collections import Counter
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from test_nxn_public_pair_gap import NEIGHBORS, public_states
from test_nxn_public_many_fixpoint import model as single_model
from test_nxn_public_overlap import oracle as overlap_oracle, source as overlap_source

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("nxn_public_subset.bend", "nxn_public_overlap.bend")


def audit():
    states = public_states()
    assert len(states) == 560
    counts = Counter()
    nonnested_cases = []
    for public, truth_layouts in sorted(states.items()):
        opened = tuple(index for index, _ in public)
        (i, ra), (j, rb) = public
        a = tuple(sorted(NEIGHBORS[i] - set(opened)))
        b = tuple(sorted(NEIGHBORS[j] - set(opened)))
        tag, safe, mines = overlap_oracle(a, b, ra, rb)
        assert tag == 1, public
        # Independent oracle: all complete mine layouts compatible with the
        # two visible numbers, not the region-bound arithmetic in Bend.
        union = set(a) | set(b)
        expected_safe = {cell for cell in union if all(
            not truth & (1 << cell) for truth in truth_layouts)}
        expected_mines = {cell for cell in union if all(
            truth & (1 << cell) for truth in truth_layouts)}
        assert set(safe) == expected_safe, public
        assert set(mines) == expected_mines, public
        single = single_model(3, public, (), opened)
        assert isinstance(single, tuple), public
        new_safe = set(safe) - set(single[1])
        new_mines = set(mines) - set(single[0])
        nested = set(a) <= set(b) or set(b) <= set(a)
        counts["nested" if nested else "nonnested"] += 1
        if new_safe or new_mines:
            counts["improved"] += 1
            if new_safe:
                counts["improved_safe"] += 1
            if new_mines:
                counts["improved_mines"] += 1
            counts["nested_gap" if nested else "nonnested_gap"] += 1
            if not nested:
                nonnested_cases.append((a, b, ra, rb))
    expected = Counter(nested=224, nonnested=336, improved=88,
                       improved_safe=64, improved_mines=64,
                       nested_gap=48, nonnested_gap=40)
    assert counts == expected, (counts, expected)
    assert len(nonnested_cases) == 40
    assert overlap_oracle((1, 3, 4), (1, 4, 5), 2, 1) == (1, (5,), (3,))
    assert len(states[((0, 2), (2, 1))]) == 16
    return nonnested_cases, counts


def check_bend(cases):
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        for name in FILES:
            (folder / name).write_bytes((GAME / name).read_bytes())
        program = folder / "check_public_pair_overlap.bend"
        program.write_text(overlap_source(cases), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            result = subprocess.run(args, cwd=folder, capture_output=True,
                                    text=True, timeout=360,
                                    env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if result.returncode:
                raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
            if len(args) == 2 and result.stdout.strip().splitlines()[-1] != "40":
                raise AssertionError(f"Expected 40, got {result.stdout}")
    witness = GAME / "nxn_public_overlap_witness.bend"
    for args in (("bend", str(witness), "--check-only"), ("bend", str(witness))):
        result = subprocess.run(args, cwd=GAME, capture_output=True,
                                text=True, timeout=360,
                                env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if result.returncode:
            raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
        if len(args) == 2 and result.stdout.strip().splitlines()[-1] != "101":
            raise AssertionError(f"Expected 101, got {result.stdout}")


def main():
    cases, counts = audit()
    print(f"PASS 560 public states: {counts['nested_gap']} nested and "
          f"{counts['nonnested_gap']} nonnested improvements", flush=True)
    if sys.argv[1:] == ["--model-only"]:
        return
    check_bend(cases)
    print("PASS 40 nonnested public-derived Bend cases and 101 witness")


if __name__ == "__main__":
    main()
