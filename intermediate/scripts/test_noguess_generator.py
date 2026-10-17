#!/usr/bin/env python3
"""End-to-end independent validation of the deterministic Bend generator.

The generated 4x4 board is replayed using the independent Python game,
not with a second invocation of the Bend game/solver.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import re
import subprocess
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
REFERENCE = ROOT / "solutions" / "noguess_reference.py"


def check() -> tuple[int, tuple[int, ...]]:
    spec = importlib.util.spec_from_file_location("noguess_reference", REFERENCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    proc = subprocess.run(
        ["bend", str(GAME / "noguess_generator.bend")],
        cwd=ROOT.parent,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
        capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, f"{proc.stdout}\n{proc.stderr}"
    match = re.fullmatch(
        r"mines=(\d+);moves=(\d+(?:,\d+)*)", proc.stdout.strip()
    )
    assert match, "generator did not provide a verified-certificate string"
    mask = int(match.group(1))
    clicks = tuple(int(i) for i in match.group(2).split(","))
    assert mask.bit_count() == 2 and mask & 0b110011 == 0
    assert clicks[0] == 0 and len(clicks) >= 2
    assert len(set(clicks)) == len(clicks), "clicks may not repeat"
    assert all(0 <= i < 16 for i in clicks)

    true_mines = frozenset(i for i in range(16) if mask & (1 << i))
    independent = module.verify_no_guess(4, 4, true_mines, 0)
    assert independent == clicks, (mask, clicks, independent)

    # The generator scans the candidate order deterministically.
    assert mask == 40960 and clicks == (0, 12, 14), (mask, clicks)
    return mask, clicks


if __name__ == "__main__":
    mask, clicks = check()
    print(f"PASS independent Bend no-guess generator replay: mask {mask}, clicks {clicks}")
