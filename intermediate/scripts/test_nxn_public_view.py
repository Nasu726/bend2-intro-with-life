#!/usr/bin/env python3
"""Bend public projection vs the independent set/BFS game oracle.

The public type contains only visible clues, flags, dimensions and status.
Finite cases do not prove arbitrary N or the absence of all side channels.
"""
from pathlib import Path
import os
import subprocess
import tempfile

from test_nxn_full_game import expected

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = (
    "game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
    "nxn_clues.bend", "nxn_step.bend", "nxn_victory.bend",
    "nxn_terminal.bend", "nxn_relocate.bend", "nxn_neighbors.bend",
    "nxn_flood.bend", "nxn_full_game.bend", "nxn_public_view.bend",
)
MASK = 0xFFFFFFFF


def traces():
    cases = []
    for n in (2, 3, 4):
        last = n * n - 1
        for mines in ((), (0,), (last,)):
            for operations in (
                (),
                (("mark", 0),),
                (("click", 0),),
                (("click", 0), ("mark", last)),
            ):
                cases.append((n, mines, operations))
    for n in (10, 17):
        for mines in ((1,), (0, 1)):
            for operations in (
                (),
                (("click", 0),),
                (("click", 0), ("mark", n*n-1)),
            ):
                cases.append((n, mines, operations))
    # Fresh 100x100: tests the dimension without scanning 10,000 cells.
    cases.append((100, (1,), (("mark", 0),)))
    return cases


def reference(n, mines, operations):
    # Reuse the separately tested independent Python set/BFS oracle.
    # Its snapshot is queried for each logical cell, never Array padding.
    if not operations or all(action == "mark" for action, _ in operations):
        return (n * 1000 + 3) & MASK
    codes = [expected(n, mines, operations, i) for i in range(n*n)]
    phase = codes[0] // 100
    if phase == 3:
        return (n * 1000 + 3) & MASK
    acc = (n * 1000 + phase) & MASK
    for i, code in enumerate(codes):
        cell = code % 100
        if cell == 1:
            acc = (acc * 131 + 200001 + i) & MASK
        elif cell >= 10:
            acc = (acc * 131 + 1 + i * 16 + cell - 10) & MASK
    return acc


def program(cases):
    lines = [
        "import Base",
        "import ./nxn_mine_words.bend as Words",
        "import ./nxn_full_game.bend as Full",
        "import ./nxn_public_view.bend as Public",
        "",
        "def encode(item: Public.Seen) -> U32:",
        "  match item:",
        "    case Public.Open{index, clue}:",
        "      (1 + index * 16 + clue : U32)",
        "    case Public.Flag{index}:",
        "      (200001 + index : U32)",
        "",
        "def fold(items: List<Public.Seen>, +acc: U32) -> U32:",
        "  match items:",
        "    case Nil{}:",
        "      acc",
        "    case item <> rest:",
        "      fold(rest, (acc * 131 + encode(item) : U32))",
        "",
        "def fingerprint(view: Public.Observation) -> U32:",
        "  match view:",
        "    case Public.Observation{n, status, seen}:",
        "      fold(seen, (n * 1000 + status : U32))",
        "",
        "def bool_code(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0",
        "",
        "def equal(a: U32, b: U32) -> U32:",
        "  bool_code(U32.is_eq(a, b))",
        "",
    ]
    for k, (n, mines, operations) in enumerate(cases):
        lines += [f"def case_{k}() -> U32:",
                  f"  board = Words.new({n})"]
        for mine in mines:
            lines.append(f"  board = Words.set_checked(board, {mine}, True{{}})")
        lines.append("  game = Full.new(board)")
        for action, index in operations:
            lines.append(f"  game = Full.{action}(game, {index})")
        lines += [
            f"  equal(fingerprint(Public.observe(game)), {reference(n, mines, operations)})",
            "",
        ]
    for start in range(0, len(cases), 8):
        lines += [
            f"def group_{start}() -> U32:",
            "  (" + " + ".join(
                f"case_{k}()" for k in range(start, min(start + 8, len(cases)))
            ) + " : U32)",
            "",
        ]
    lines += [
        "def main() -> U32:",
        "  (" + " + ".join(
            f"group_{k}()" for k in range(0, len(cases), 8)
        ) + " : U32)",
    ]
    return "\n".join(lines) + "\n"


def main():
    cases = traces()
    assert len(cases) == 49, len(cases)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name in FILES:
            (root / name).write_bytes((GAME / name).read_bytes())
        source = root / "public_view_test.bend"
        source.write_text(program(cases), encoding="utf-8")
        for args in (("bend", str(source), "--check-only"),
                     ("bend", str(source))):
            print(f"CHECK public observation {len(cases)} / {args[-1]}", flush=True)
            result = subprocess.run(
                args, cwd=root, capture_output=True, text=True, timeout=360,
                env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if result.returncode:
                raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
            if len(args) == 2 and result.stdout.strip().splitlines()[-1] != str(len(cases)):
                raise AssertionError(
                    f"Expected {len(cases)} exact fingerprints, got {result.stdout}"
                )
    print(f"PASS {len(cases)} public-only observation checks")


if __name__ == "__main__":
    main()
