#!/usr/bin/env python3
"""N=10 two-region Bend playthrough versus independent Python set/BFS model.

This verifies a 90-safe-cell cascade and terminal victory, not a GUI,
100x100 performance, arbitrary-size no-guess solver, or a formal proof.
"""
import os
from pathlib import Path
import subprocess
import tempfile

from test_nxn_full_game import expected, source, FILES, GAME

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



def check_bend_boundaries():
    """Exercise the actual Bend engine at intermediate and terminal states.

    The original demonstration checks only the final 110. These cases also
    compare flags, mine loss, first-click relocation and frozen terminal input.
    Each expected value comes from the independent Python set/BFS model.
    """
    wall = tuple(range(50, 60))
    cases = (
        (10, wall, (("click", 0),), 49, 12),
        (10, wall, (("click", 0), ("mark", 99), ("click", 99)), 99, 1),
        (10, wall, (("click", 0), ("mark", 99), ("click", 99),
                    ("mark", 99), ("click", 99)), 99, 110),
        (10, wall, (("click", 0), ("click", 50), ("click", 99)), 99, 200),
        (10, wall, (("click", 50),), 50, 11),
        (10, wall, (("click", 99), ("click", 0)), 0, 110),
        (10, wall, (("click", 0), ("click", 99), ("click", 50)), 50, 100),
        (10, wall, (("mark", 99),), 99, 300),
        (10, wall, (("click", 100),), 0, 300),
        (10, wall, (("click", 127),), 0, 300),
        (10, wall, (("click", 0), ("mark", 99), ("mark", 99),
                    ("click", 99)), 99, 110),
        (10, wall, (("click", 0), ("click", 50)), 50, 200),
        (10, wall, (("click", 0), ("mark", 50), ("click", 50)), 50, 1),
        (10, wall, (("click", 0), ("mark", 50), ("click", 50),
                    ("mark", 50), ("click", 50)), 50, 200),
        (10, wall, (("click", 0), ("click", 99), ("mark", 50)), 50, 100),
        (10, wall, (("click", 50), ("click", 0)), 0, 200),
        (10, wall, (("click", 0), ("mark", 49)), 49, 12),
    )
    for n, mines, operations, probe, value in cases:
        assert expected(n, mines, operations, probe) == value
    checks = tuple((n, mines, operations, probe)
                   for n, mines, operations, probe, _ in cases)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        # Running 17 full-game traces as one Bend program exceeded 360 s.
        # Preserve all 17 oracle cases; compile and run batches of at most six.
        for start in range(0, len(checks), 6):
            batch = checks[start:start + 6]
            program = directory / f"check_playthrough_{start}.bend"
            program.write_text(source(batch), encoding="utf-8")
            for args in (("bend", str(program), "--check-only"),
                         ("bend", str(program))):
                result = subprocess.run(
                    args, cwd=directory, capture_output=True, text=True,
                    timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
                )
                if result.returncode:
                    raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
                if len(args) == 2 and result.stdout.strip().splitlines()[-1] != str(len(batch)):
                    raise AssertionError(
                        f"Expected {len(batch)} Bend/Python matches: {result.stdout}"
                    )
    print(f"PASS {len(checks)} N=10 Bend/Python boundary traces")



def check_demo_variants():
    """Typecheck and execute the two documented Bend scenario functions."""
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        (directory / DEMO.name).write_bytes(DEMO.read_bytes())
        program = directory / "check_playthrough_variants.bend"
        program.write_text(
            "import Base\n"
            "import ./nxn_playthrough.bend as Demo\n\n"
            "def main() -> U32:\n"
            "  (Demo.flag_block_then_win() + Demo.relocated_mine_loss() : U32)\n",
            encoding="utf-8",
        )
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            result = subprocess.run(
                args, cwd=directory, capture_output=True, text=True,
                timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if result.returncode:
                raise AssertionError(f"{args}: {result.stdout}\\n{result.stderr}")
            if len(args) == 2 and result.stdout.strip().splitlines()[-1] != "310":
                raise AssertionError(f"Expected 110+200 from Bend demos: {result.stdout}")
    print("PASS 2 named Bend playthrough variants: flag win and relocated loss")

def main():
    check_oracle()
    check_demo_variants()
    check_bend_boundaries()
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
