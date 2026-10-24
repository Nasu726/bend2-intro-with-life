#!/usr/bin/env python3
"""Finite differential test for Bend N x N zero cascade, not a proof."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = ("game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
         "nxn_clues.bend", "nxn_neighbors.bend", "nxn_step.bend",
         "nxn_flood.bend")


def oracle(n, mines, flags, click, probe):
    mines, flags = set(mines), set(flags)
    opened = {}
    if 0 <= click < n*n and click not in flags and click not in mines:
        pending = [click]
        while pending:
            i = pending.pop()
            if i in opened or i in flags or i in mines:
                continue
            x, y = i % n, i // n
            neighbors = [j for j in range(n*n)
                         if j != i and abs(j % n - x) <= 1
                         and abs(j // n - y) <= 1]
            clue = sum(j in mines for j in neighbors)
            opened[i] = clue
            if clue == 0:
                pending.extend(neighbors)
    if not 0 <= probe < n*n:
        return 99
    if probe in opened:
        return 10 + opened[probe]
    return 1 if probe in flags else 0


def cases():
    configs = [
        (2, (), (), 0, (0, 1, 3)),
        (2, (3,), (), 0, (0, 1, 2, 3)),
        (2, (0,), (), 0, (0, 1)),
        (3, (8,), (), 0, (0, 1, 4, 7, 8)),
        (3, (1,), (), 0, (0, 1, 8)),
        (3, (8,), (1,), 0, (0, 1, 4, 7)),
        (4, (15,), (), 0, (0, 5, 14, 15)),
        (4, (15,), (1,), 0, (0, 1, 5, 14)),
        (4, (1,), (), 0, (0, 1, 15)),
        (10, (1,), (), 0, (0, 1, 99, 100, 127)),
        (10, (99,), (), 0, (0, 55, 98, 99)),
        (17, (1,), (), 0, (0, 1, 288)),
        (100, (1,), (), 0, (0, 1, 9999, 10000)),
        (10, (99,), (), 100, (0, 99)),
        (10, (99,), (), 127, (0, 99)),
    ]
    return [(n, mines, flags, click, probe)
            for n, mines, flags, click, probes in configs for probe in probes]


def source(checks):
    lines = [
        "import Base", "import ./nxn_mine_words.bend as Words",
        "import ./nxn_step.bend as Step",
        "import ./nxn_flood.bend as Flood", "",
        "def as_one(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
    ]
    for k, (n, mines, flags, click, probe) in enumerate(checks):
        lines.extend((f"def case_{k}() -> U32:", f"  board = Words.new({n})"))
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  state = Step.new(board)")
        for flag in flags:
            lines.append(f"  state = Step.mark(state, {flag})")
        lines.extend((
            f"  state = Flood.reveal(state, {click})",
            f"  as_one(U32.is_eq(Step.snapshot(state, {probe}), "
            f"{oracle(n, mines, flags, click, probe)}))", "",
        ))
    for start in range(0, len(checks), 8):
        lines.extend((
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(f"case_{i}()" for i in
                             range(start, min(start+8, len(checks)))) + " : U32)", "",
        ))
    lines.extend((
        "def main() -> U32:",
        "  (" + " + ".join(f"group_{i}()" for i in range(0, len(checks), 8))
        + " : U32)",
    ))
    return "\n".join(lines) + "\n"


def main():
    checks = cases()
    assert len(checks) >= 40
    assert oracle(3, (8,), (), 0, 7) == 11
    assert oracle(4, (15,), (1,), 0, 1) == 1
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_nxn_flood.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            print(f"CHECK N x N zero flood: {len(checks)} cases / {args[-1]}", flush=True)
            proc = subprocess.run(args, cwd=directory, capture_output=True,
                                  text=True, timeout=360,
                                  env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if proc.returncode:
                raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
            if len(args) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(
                    f"Expected {len(checks)} matches, got {proc.stdout}")
    print(f"PASS {len(checks)} independent Bend flood checks")


if __name__ == "__main__":
    main()
