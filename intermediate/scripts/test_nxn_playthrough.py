#!/usr/bin/env python3
"""N=10 two-region Bend playthrough versus independent Python set/BFS model.

This verifies a 90-safe-cell cascade and terminal victory, not a GUI,
100x100 performance, arbitrary-size no-guess solver, or a formal proof.
"""
import os
from pathlib import Path
import subprocess

from test_nxn_full_game import expected

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "minesweeper" / "nxn_playthrough.bend"


def check_oracle():
    wall = tuple(range(50, 60))
    first = (("click", 0),)
    won = first + (("click", 99),)
    assert expected(10, wall, first, 49) == 12  # Right-edge number 2.
    assert expected(10, wall, first, 99) == 0   # Bottom is still hidden.
    assert expected(10, wall, won, 99) == 110  # Won, open zero.
    assert expected(10, wall, won + (("click", 50),), 50) == 100
    assert expected(10, wall, first + (("mark", 99), ("click", 99)), 99) == 1


def main():
    check_oracle()
    for args in (("bend", str(DEMO), "--check-only"), ("bend", str(DEMO))):
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                timeout=360,
                                env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if result.returncode:
            raise AssertionError(f"{args}: {result.stdout}\\n{result.stderr}")
        if len(args) == 2 and result.stdout.strip().splitlines()[-1] != "110":
            raise AssertionError(f"10x10 playthrough must win with 110: {result.stdout}")
    print("PASS N=10 mine-wall playthrough: 50+40 safe cells, victory 110")


if __name__ == "__main__":
    main()
