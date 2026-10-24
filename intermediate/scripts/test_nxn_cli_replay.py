#!/usr/bin/env python3
"""Check the real 10x10 Bend CLI against a separate set/BFS game model.

This checks command replay and the *entire* visible 100-cell board, including
the 28 Array padding slots being omitted. It does not test GUI or File saves.
"""
import os
from pathlib import Path
import subprocess

from test_nxn_full_game import expected

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "minesweeper" / "nxn_cli_replay.bend"
MINES = (11, 12, 22, 34, 45, 56, 67, 78, 89, 99)


def expected_board(commands):
    operations = []
    for command in commands:
        if command == "r":
            operations.clear()
        elif len(command) > 1 and command[0] in "cf" and command[1:].isdigit():
            operations.append(("click" if command[0] == "c" else "mark",
                               int(command[1:])))
    phase = expected(10, MINES, operations, 0) // 100
    if phase == 3:
        return "Fresh: first click with c0..c99"
    heading = {0: "Playing", 1: "Won", 2: "Lost"}[phase]
    visible = []
    for index in range(100):
        code = expected(10, MINES, operations, index) % 100
        visible.append("." if code == 0 else "F" if code == 1 else str(code - 10))
    rows = [" ".join(visible[i:i + 10]) for i in range(0, 100, 10)]
    return "\n".join([heading, *rows])


def main():
    env = dict(os.environ, BEND_NO_TELEMETRY="1")
    checked = subprocess.run(
        ["bend", str(ENTRY), "--check-only"],
        cwd=ROOT.parent, text=True, capture_output=True, timeout=180, env=env,
    )
    assert checked.returncode == 0, (checked.stdout, checked.stderr)

    traces = (
        (),
        ("f0",),
        ("c100",),
        ("c127",),
        ("c0",),
        ("c0", "f1"),
        ("c0", "f1", "c1"),
        ("c0", "f1", "f1", "c1"),
        ("c0", "c11"),
        ("c0", "c11", "f2", "c2"),
        ("c11",),
        ("c0", "r"),
        ("c0", "r", "c11"),
        ("c0", "c100", "f127", "cx", "f"),
        ("c0", "f99", "c99", "f99", "c99"),
    )
    seen = set()
    for trace in traces:
        run = subprocess.run(
            ["bend", str(ENTRY), *trace], cwd=ROOT.parent,
            text=True, capture_output=True, timeout=180, env=env,
        )
        assert run.returncode == 0, (trace, run.stdout, run.stderr)
        actual = run.stdout.strip()
        wanted = expected_board(trace)
        assert actual == wanted, (
            f"CLI trace {trace!r} differed\nexpected:\n{wanted}\nactual:\n{actual}\n"
            f"stderr:\n{run.stderr}"
        )
        seen.add(wanted.splitlines()[0].split(":")[0])
        if wanted.startswith(("Playing", "Won", "Lost")):
            assert len(actual.splitlines()) == 11, (trace, actual)
            assert all(len(row.split()) == 10 for row in actual.splitlines()[1:])
    assert {"Fresh", "Playing", "Lost"} <= seen, seen
    print(f"PASS {len(traces)} full-board Bend CLI replay comparisons (10x10, M=10)")


if __name__ == "__main__":
    main()
