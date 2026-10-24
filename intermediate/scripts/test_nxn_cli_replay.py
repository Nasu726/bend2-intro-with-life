#!/usr/bin/env python3
"""Real Bend CLI replay versus an independent Python set/BFS game oracle.

Finite tests on a fixed N=10 mine wall; not an interactive terminal, GUI,
N x N generator, exhaustive proof or 100 x 100 performance benchmark.
"""
import os
from pathlib import Path
import subprocess

from test_nxn_full_game import expected

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "minesweeper" / "nxn_cli_replay.bend"
WALL = tuple(range(50, 60))
MAX_U32 = 2**32 - 1

# The first token is a probe index; remaining tokens are commands.
CASES = (
    ("49", "c0"),
    ("99", "c0"),
    ("99", "c0", "c99"),
    ("99", "c0", "f99", "c99"),
    ("99", "c0", "f99", "c99", "f99", "c99"),
    ("99", "c0", "c50", "c99"),
    ("50", "c50"),
    ("0", "c99", "c0"),
    ("50", "c0", "c99", "c50"),
    ("99", "c0", "r"),
    ("99", "c0", "r", "c99"),
    ("99", "c0", "ignored", "c99"),
    ("99", "c0", "c-1", "fgarbage", "c99"),
    ("99", "c0", "c100", "f127", "c99"),
    ("100", "c0"),
    ("99", "f99", "c0"),
    ("99", "c0", "r", "f99", "c99"),
    (),
    ("not-a-number", "c0"),
)

def oracle(tokens):
    if not tokens:
        return 999
    try:
        probe = int(tokens[0])
    except ValueError:
        return 999
    if not 0 <= probe <= MAX_U32:
        return 999
    operations = []
    for command in tokens[1:]:
        if command == "r":
            operations.clear()
            continue
        if not command.startswith(("c", "f")):
            continue
        digits = command[1:]
        if not digits.isdecimal():
            continue
        index = int(digits)
        if index > MAX_U32:
            continue
        operations.append(("click" if command[0] == "c" else "mark", index))
    return expected(10, WALL, tuple(operations), probe)

def invoke(*arguments):
    process = subprocess.run(
        ("bend", str(CLI), *arguments), cwd=ROOT,
        capture_output=True, text=True, timeout=360,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
    )
    if process.returncode:
        raise AssertionError(
            f"CLI {arguments} failed: {process.stdout}\\n{process.stderr}"
        )
    return process.stdout.strip().splitlines()[-1]

def main():
    check = subprocess.run(
        ("bend", str(CLI), "--check-only"), cwd=ROOT,
        capture_output=True, text=True, timeout=360,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
    )
    if check.returncode:
        raise AssertionError(f"CLI typecheck failed: {check.stdout}\\n{check.stderr}")
    for tokens in CASES:
        actual = invoke(*tokens)
        wanted = str(oracle(tokens))
        if actual != wanted:
            raise AssertionError(f"{tokens}: Bend={actual}, Python={wanted}")
    assert oracle(("99", "c0", "c99")) == 110
    assert oracle(("99", "c0", "r")) == 300
    print(f"PASS {len(CASES)} N=10 Bend CLI/Python independent replay cases")

if __name__ == "__main__":
    main()
