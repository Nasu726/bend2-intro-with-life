#!/usr/bin/env python3
"""Independent finite Bend N x N clue checks (not a universal proof).

The oracle counts neighbors from a Python set of mine positions. It does
not call the packed-word oracle or reuse Bend's neighbor implementation.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"


def cases():
    checks = []

    def add(n, mines, index):
        board = f"Mines.new({n})"
        for mine in mines:
            board = f"Mines.set_checked({board}, {mine}, True{{}})"
        if 0 <= index < n*n:
            x, y = index % n, index // n
            expected = sum(
                j != index and max(abs(j % n-x), abs(j//n-y)) == 1
                for j in mines
            )
        else:
            expected = 99
        checks.append(
            f"bit(U32.is_eq(Clue.result(Clue.checked({board}, {index})), {expected}))"
        )

    # All 16 two-by-two mine configurations and all four target cells.
    for mask in range(16):
        mines = tuple(i for i in range(4) if mask & (1 << i))
        for index in range(4):
            add(2, mines, index)

    # Corners, edges, word boundaries, fully mined 3x3, and 100x100.
    for n in (3, 10, 17, 100):
        cells = n*n
        configurations = [
            (), (0,), (cells-1,), (0, n+1, cells-1),
            tuple(i for i in (31, 32, 63, 64) if i < cells),
            tuple(range(cells)) if n == 3 else
            tuple(range(0, cells, max(1, cells//5))),
        ]
        indices = sorted({0, n-1, n, cells//2, cells-1, 31, 32} &
                         set(range(cells)))
        for mines in configurations:
            for index in indices:
                add(n, mines, index)
        for index in (cells, cells+27, 4294967295):
            add(n, (0, cells-1), index)
    return checks


def program(checks):
    groups = [
        f"def group_{i}() -> U32:\n  (" +
        " + ".join(checks[i:i+4]) + " : U32)"
        for i in range(0, len(checks), 4)
    ]
    return (
        "import Base\n"
        "import ./nxn_geometry.bend as Geo\n"
        "import ./nxn_mine_words.bend as Mines\n"
        "import ./nxn_clues.bend as Clue\n"
        "def bit(b: Bool) -> U32:\n"
        "  match b:\n"
        "    case True{}:\n      1\n"
        "    case False{}:\n      0\n\n" +
        "\n\n".join(groups) +
        "\n\ndef main() -> U32:\n  (" +
        " + ".join(f"group_{i}()" for i in range(0, len(checks), 4)) +
        " : U32)\n"
    )


def run(*args, cwd):
    proc = subprocess.run(
        args, cwd=cwd, text=True, capture_output=True, timeout=240,
        env=dict(os.environ, BEND_NO_TELEMETRY="1")
    )
    if proc.returncode:
        raise AssertionError(f"{args}: {proc.stdout}\n{proc.stderr}")
    return proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""


def main():
    checks = cases()
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)
        for name in ("nxn_geometry.bend", "nxn_mine_words.bend", "nxn_clues.bend"):
            shutil.copyfile(GAME / name, folder / name)
        entry = folder / "check_clues.bend"
        entry.write_text(program(checks), encoding="utf-8")
        run("bend", str(entry), "--check-only", cwd=folder)
        found = run("bend", str(entry), cwd=folder)
        if found != str(len(checks)):
            raise AssertionError(f"N x N clues: {found} != {len(checks)}")
        if run("bend", str(folder / "nxn_clues.bend"), cwd=folder) != "2":
            raise AssertionError("N x N clue example did not return 2")
    print(f"PASS Bend N x N clues: {len(checks)} independent finite checks")


if __name__ == "__main__":
    main()
