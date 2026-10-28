#!/usr/bin/env python3
"""Independent finite Bend audit of post-first-click placement and game."""
import os
from pathlib import Path
import subprocess
import tempfile
from test_nxn_full_game import expected as expected_full_game

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
FILES = (
    "game.bend", "nxn_geometry.bend", "nxn_mine_words.bend",
    "nxn_clues.bend", "nxn_step.bend", "nxn_victory.bend",
    "nxn_terminal.bend", "nxn_neighbors.bend", "nxn_flood.bend",
    "nxn_lazy_placement.bend", "nxn_lazy_game.bend",
)


def place(n, count, seed, clicked):
    if not 2 <= n <= 100 or not 0 <= clicked < n*n or not 0 <= count < n*n:
        return None
    rng, slots, left = seed & 0xffffffff, n*n-1, count
    mines = set()
    for index in range(n*n):
        if index == clicked:
            continue
        rng = (1664525 * rng + 1013904223) & 0xffffffff
        if rng % slots < left:
            mines.add(index)
            left -= 1
        slots -= 1
    assert left == slots == 0 and len(mines) == count
    assert clicked not in mines
    return mines


def placement_cases():
    cases = []
    for n in (2, 3, 4, 10):
        for seed in (0, 1, 42):
            for count in (0, 1, n*n-1):
                clicked = (seed + count) % (n*n)
                mines = place(n, count, seed, clicked)
                for probe in sorted({0, clicked, n*n-1}):
                    cases.append((n, count, seed, clicked, probe, int(probe in mines)))
    for n in (17, 100):
        for count, seed, clicked in ((1, 17, 0), (n*n-1, 42, n*n-1)):
            mines = place(n, count, seed, clicked)
            for probe in (clicked, 0):
                cases.append((n, count, seed, clicked, probe, int(probe in mines)))
    cases.extend((
        (1, 0, 0, 0, 0, 2), (101, 0, 0, 0, 0, 2),
        (2, 4, 0, 0, 0, 2), (2, 1, 0, 4, 0, 2),
        (10, 2, 0, 127, 0, 2),
    ))
    return cases


def game_cases():
    cases = []
    traces = (
        (("mark", 0), ("click", 0)),
        (("click", 100), ("click", 0)),
        (("click", 0), ("click", 1)),
        (("mark", 1), ("click", 0), ("mark", 1), ("click", 1)),
        (("click", 0), ("mark", 1), ("click", 1)),
    )
    for n in (2, 3, 4):
        for count in (0, 1, n*n-1):
            for seed in (0, 42):
                for trace in traces:
                    mines = place(n, count, seed, 0)
                    expected = expected_full_game(n, mines, trace, n*n-1)
                    cases.append((n, count, seed, trace, n*n-1, expected))
    cases.extend((
        (2, 4, 0, (("click", 0),), 0, 300),
        (10, 1, 0, (("click", 127),), 0, 300),
        (1, 0, 0, (("click", 0),), 0, 300),
        (2, 3, 0, (("click", 0),), 0, 113),
    ))
    return cases


def program(kind, checks):
    lines = [
        "import Base",
        "import ./nxn_lazy_placement.bend as Placement" if kind == "placement"
        else "import ./nxn_lazy_game.bend as Game",
        "",
        "def one_if_true(equal: Bool) -> U32:",
        "  match equal:", "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def one_if_equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))", "",
    ]
    for i, row in enumerate(checks):
        lines.append(f"def case_{i}() -> U32:")
        if kind == "placement":
            n, count, seed, clicked, probe, expected = row
            lines.append(
                f"  one_if_equal(Placement.inspect(Placement.place({n}, {count}, {seed}, {clicked}), {probe}), {expected})"
            )
        else:
            n, count, seed, trace, probe, expected = row
            lines.append(f"  game = Game.new({n}, {count}, {seed})")
            for action, index in trace:
                lines.append(f"  game = Game.{action}(game, {index})")
            lines.append(f"  one_if_equal(Game.snapshot(game, {probe}), {expected})")
        lines.append("")
    for start in range(0, len(checks), 8):
        lines.append(f"def group_{start}() -> U32:")
        lines.append("  (" + " + ".join(
            f"case_{i}()" for i in range(start, min(start+8, len(checks)))
        ) + " : U32)")
        lines.append("")
    lines.append("def main() -> U32:")
    lines.append("  (" + " + ".join(
        f"group_{i}()" for i in range(0, len(checks), 8)
    ) + " : U32)")
    return "\n".join(lines) + "\n"


def check_bend(kind, checks):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name in FILES:
            (work / name).write_bytes((GAME / name).read_bytes())
        source = work / f"check_lazy_{kind}.bend"
        source.write_text(program(kind, checks), encoding="utf-8")
        for command in (("bend", str(source), "--check-only"),
                        ("bend", str(source))):
            print(f"CHECK lazy {kind}: {len(checks)} cases / {command[-1]}", flush=True)
            proc = subprocess.run(
                command, cwd=work, capture_output=True, text=True, timeout=360,
                env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if proc.returncode:
                raise AssertionError(f"{command}: {proc.stdout}\n{proc.stderr}")
            if len(command) == 2 and proc.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(f"Expected {len(checks)} matches: {proc.stdout}")


def main():
    source = (GAME / "nxn_lazy_game.bend").read_text(encoding="utf-8")
    assert "Fresh{n: U32, mine_count: U32, seed: U32}" in source
    assert "Fresh{board:" not in source
    placement, game = placement_cases(), game_cases()
    check_bend("placement", placement)
    check_bend("game", game)
    print(f"PASS lazy placement {len(placement)} / game {len(game)} Bend cases")


if __name__ == "__main__":
    main()
