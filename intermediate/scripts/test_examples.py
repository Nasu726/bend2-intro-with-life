#!/usr/bin/env python3
"""Typecheck intermediate Bend examples, check outputs and proof verdict."""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "src"
EXPECTED = {
    "01_set.bend": "1",
    "02_map.bend": "7",
    "03_list.bend": "3n",
    "05_marking.bend": "0n",
    "06_parallel.bend": "256",
    "09_minesweeper_status.bend": "1",
    "10_board_neighbors.bend": "2",
    "14_local_inference.bend": "10",
    "15_string_parse.bend": "42",
    "16_map_set_api.bend": "3n",
    "17_list_pipeline.bend": "3n",
    "18_array_mutations.bend": "17",
    "20_process_run.bend": "0",
    "21_io_fork.bend": "7",
    "22_result_and_game.bend": "1",
    "23_cell_hit_test.bend": "10",
    "24_bool_proofs.bend": "1",
    "25_either_case.bend": "7",
    "28_chan_roundtrip.bend": "9",
    "30_array_clone.bend": "22",
    "31_image_quadrants.bend": "16711680",
    "32_mouse_events.bend": "10",
    "33_nat_induction.bend": "0",
    "34_mine_mask_law.bend": "1",
    "35_string_fields.bend": "2n",
    "36_map_missing.bend": "1",
    "37_u32_dimension.bend": "1",
}

def run(*args):
    p = subprocess.run(args, text=True, capture_output=True, timeout=180,
                       cwd=ROOT.parent,
                       env=dict(os.environ, BEND_NO_TELEMETRY="1"))
    if p.returncode != 0:
        raise AssertionError(f"{args} exited {p.returncode}:\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()

def verify_full_neighbor_table(game_dir):
    """Independent 4x4 truth table: every ordered pair of cells, not just corners.

    Generate a Bend test program rather than trusting a Python copy of the
    implementation. Each of 16 rows returns an exact 16-bit adjacency mask.
    """
    rows = []
    checks = []
    for y in range(4):
        for x in range(4):
            i = y * 4 + x
            terms = []
            signature = 0
            for v in range(4):
                for u in range(4):
                    j = v * 4 + u
                    terms.append(
                        f"(bit(Board.neighbor({x}, {y}, {u}, {v})) * {1 << j} : U32)"
                    )
                    if (x, y) != (u, v) and abs(x - u) <= 1 and abs(y - v) <= 1:
                        signature |= 1 << j
            rows.append(f"def row_{i}() -> U32:\n  (" + " + ".join(terms) + " : U32)")
            checks.append(f"bit(U32.is_eq(row_{i}(), {signature}))")
    source = (
        "import Base\nimport ./board.bend as Board\n"
        "def bit(b: Bool) -> U32:\n"
        "  match b:\n    case True{}:\n      1\n"
        "    case False{}:\n      0\n\n"
        + "\n\n".join(rows)
        + "\n\ndef main() -> U32:\n  ("
        + " + ".join(checks)
        + " : U32)\n"
    )
    with tempfile.TemporaryDirectory() as td:
        path = pathlib.Path(td)
        shutil.copyfile(game_dir / "game.bend", path / "game.bend")
        shutil.copyfile(game_dir / "board.bend", path / "board.bend")
        (path / "check_board.bend").write_text(source, encoding="utf-8")
        result = run("bend", str(path / "check_board.bend")).splitlines()[-1]
        if result != "16":
            raise AssertionError(f"4x4 nonwrapping adjacency table failed: {result}")
        print("PASS all 256 ordered 4x4 cell pairs against independent oracle", flush=True)


def verify_dense_board(game_dir):
    """Independent clues, all valid indices, and invalid-index regression checks."""
    def neighbors(mask, x, y):
        return sum(
            (mask >> (4*v+u)) & 1
            for v in range(4) for u in range(4)
            if (u, v) != (x, y) and abs(x-u) <= 1 and abs(y-v) <= 1
        )
    expressions = []
    for mask in (0, 1, 33, 32768, 21845, 65535):
        for y in range(4):
            for x in range(4):
                expressions.append(
                    f"bit(U32.is_eq(Board4.clue({mask}, {x}, {y}), {neighbors(mask,x,y)}))"
                )
    for mine_index in range(16):
        mask = 1 << mine_index
        x, y = mine_index % 4, mine_index // 4
        expressions.append(f"bit(U32.is_eq(Board4.clue({mask}, {x}, {y}), 0))")
    for i in range(16):
        expressions.append(
            f"bit(U32.is_eq(show(Board4.visible_at("
            f"Board4.toggle_checked(Board4.new_state(0), {i}), {i})), 1))"
        )
        expressions.append(
            f"bit(U32.is_eq(show(Board4.visible_at("
            f"Board4.reveal_checked(Board4.new_state(0), {i}, 3), {i})), 13))"
        )
    for i in (16, 17, 31, 32, 65535):
        expressions.append(
            f"bit(U32.is_eq(show(Board4.visible_at("
            f"Board4.toggle_checked(Board4.new_state(0), {i}), 0)), 0))"
        )
        expressions.append(
            f"bit(U32.is_eq(show(Board4.visible_at("
            f"Board4.reveal_checked(Board4.new_state(0), {i}, 3), 0)), 0))"
        )
    expected = len(expressions)
    program = (
        "import Base\nimport ./game.bend as Game\n"
        "import ./board.bend as Board\nimport ./board4.bend as Board4\n"
        "def bit(b: Bool) -> U32:\n"
        "  match b:\n    case True{}:\n      1\n    case False{}:\n      0\n"
        "def show(s: Game.Square) -> U32:\n"
        "  match s:\n    case Game.Hidden{}:\n      0\n"
        "    case Game.Flag{}:\n      1\n"
        "    case Game.Open{clue}:\n      (10 + clue : U32)\n\n"
        + "\n\n".join(
            f"def check_{i}() -> U32:\n  ("
            + " + ".join(expressions[i:i+8]) + " : U32)"
            for i in range(0, len(expressions), 8)
        )
        + "\n\ndef main() -> U32:\n  ("
        + " + ".join(f"check_{i}()" for i in range(0, len(expressions), 8))
        + " : U32)\n"
    )
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td)
        for name in ("game.bend", "board.bend", "board4.bend", "session.bend"):
            shutil.copyfile(game_dir / name, out / name)
        f = out / "dense_oracle.bend"
        f.write_text(program, encoding="utf-8")
        found = run("bend", str(f)).splitlines()[-1]
        if found != str(expected):
            raise AssertionError(f"Full-board oracle expected {expected}; got {found}")
        print(f"PASS dense board oracle: {expected} clue/index checks", flush=True)


def verify_sessions(game_dir):
    """Check complete click transitions against a separate Python game oracle."""
    def clue(mask, index):
        x, y = index % 4, index // 4
        return sum(
            (mask >> (4*v+u)) & 1
            for v in range(4) for u in range(4)
            if (u, v) != (x, y) and abs(x-u) <= 1 and abs(y-v) <= 1
        )
    checks = []
    for mines in (0, 1, 33, 65532, 65534, 65535):
        safe_count = sum(not (mines & (1 << i)) for i in range(16))
        for index in (0, 1, 5, 15, 16):
            mined = index < 16 and bool(mines & (1 << index))
            phase = 0 if index >= 16 else (2 if mined else (1 if safe_count == 1 else 0))
            expr = f"Session.click(Session.new({mines}), {index})"
            checks.append(f"bit(U32.is_eq(phase_code(Session.phase_of({expr})), {phase}))")
            if index < 16:
                visible = 0 if mined else 10 + clue(mines, index)
                checks.append(f"bit(U32.is_eq(square_code(Session.read_square({expr}, {index})), {visible}))")
        for index in (0, 5):
            expr = f"Session.click(Session.mark(Session.new({mines}), {index}), {index})"
            checks.append(f"bit(U32.is_eq(phase_code(Session.phase_of({expr})), 0))")
            checks.append(f"bit(U32.is_eq(square_code(Session.read_square({expr}, {index})), 1))")
    # Two safe cells: one safe click is not a victory, both are. Flags are not
    # substitutes for opening the safe squares, and are reversible.
    checks += [
        "bit(U32.is_eq(phase_code(Session.phase_of(Session.click(Session.new(65532), 0))), 0))",
        "bit(U32.is_eq(phase_code(Session.phase_of(Session.click(Session.click(Session.new(65532), 0), 1))), 1))",
        "bit(U32.is_eq(phase_code(Session.phase_of(Session.click(Session.mark(Session.new(65534), 0), 0))), 0))",
        "bit(U32.is_eq(phase_code(Session.phase_of(Session.click(Session.mark(Session.mark(Session.new(65534), 0), 0), 0))), 1))",
        "bit(U32.is_eq(phase_code(Session.phase_of(Session.click(Session.click(Session.new(1), 0), 5))), 2))",
        "bit(U32.is_eq(phase_code(Session.phase_of(Session.mark(Session.click(Session.new(1), 0), 5))), 2))",
        "bit(U32.is_eq(phase_code(Session.phase_of(Session.click(Session.click(Session.new(65534), 0), 1))), 1))",
        "bit(U32.is_eq(phase_code(Session.phase_of(Session.mark(Session.click(Session.new(65534), 0), 1))), 1))",
    ]
    program = (
        "import Base\nimport ./game.bend as Game\n"
        "import ./board.bend as Board\nimport ./board4.bend as Board4\n"
        "import ./session.bend as Session\n"
        "def bit(b: Bool) -> U32:\n"
        "  match b:\n    case True{}:\n      1\n    case False{}:\n      0\n"
        "def phase_code(p: Session.Phase) -> U32:\n"
        "  match p:\n    case Session.Playing{}:\n      0\n"
        "    case Session.Won{}:\n      1\n    case Session.Lost{}:\n      2\n"
        "def square_code(s: Game.Square) -> U32:\n"
        "  match s:\n    case Game.Hidden{}:\n      0\n"
        "    case Game.Flag{}:\n      1\n"
        "    case Game.Open{clue}:\n      (10 + clue : U32)\n"
        + "\n\n".join(
            f"def check_{i}() -> U32:\n  ("
            + " + ".join(checks[i:i+6]) + " : U32)"
            for i in range(0, len(checks), 6)
        )
        + "\n\ndef main() -> U32:\n  ("
        + " + ".join(f"check_{i}()" for i in range(0, len(checks), 6))
        + " : U32)\n"
    )
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td)
        for name in ("game.bend", "board.bend", "board4.bend", "session.bend"):
            shutil.copyfile(game_dir / name, out / name)
        filename = out / "session_oracle.bend"
        filename.write_text(program, encoding="utf-8")
        observed = run("bend", str(filename)).splitlines()[-1]
        if observed != str(len(checks)):
            raise AssertionError(f"Session oracle expected {len(checks)} checks; got {observed}")
        print(f"PASS pure session oracle: {len(checks)} transition checks", flush=True)

def main():
    if not shutil.which("bend"):
        print("ERROR: bend not on PATH", file=sys.stderr)
        return 2
    files = sorted(SAMPLES.glob("*.bend"))
    if not files:
        raise AssertionError("No Bend examples")
    errors = []
    for file in files:
        try:
            run("bend", str(file), "--check-only")
            print(f"PASS typecheck {file.name}", flush=True)
        except AssertionError as exc:
            errors.append(str(exc))
    if errors:
        raise AssertionError("\n\n".join(errors))
    for file, result in EXPECTED.items():
        value = run("bend", str(SAMPLES / file)).splitlines()[-1]
        if value != result:
            raise AssertionError(f"{file} expected {result}; got {value}")
        print(f"PASS value {file} = {value}", flush=True)
    with tempfile.TemporaryDirectory() as td:
        p = subprocess.run(["bend", str(SAMPLES / "12_file_write.bend")],
                           text=True, capture_output=True, timeout=180, cwd=td,
                           env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if p.returncode != 0:
            raise AssertionError(f"File sample failed: {p.stdout}\n{p.stderr}")
        saved = pathlib.Path(td) / "sample_board.txt"
        if saved.read_text() != "board-size=4\nmines=1,1\n":
            raise AssertionError("File sample wrote unexpected content")
        print("PASS file write/open/close", flush=True)
        read = subprocess.run(["bend", str(SAMPLES / "13_file_read.bend")],
                              text=True, capture_output=True, timeout=180, cwd=td,
                              env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if read.returncode != 0:
            raise AssertionError(f"File read failed: {read.stdout}\n{read.stderr}")
        if read.stdout.strip() != "board-size=4\nmines=1,1":
            raise AssertionError(f"Unexpected read content: {read.stdout!r}")
        print("PASS file read/open/close", flush=True)

    env_output = run("bend", str(SAMPLES / "19_environment.bend"))
    if not env_output.splitlines()[-1].isdigit():
        raise AssertionError(f"Environment example did not return a numeric length: {env_output!r}")
    print("PASS environment variable Result example", flush=True)

    # The game requirements are NOT sample-local examples: import every claim,
    # and check the independent PROOF.bend with Bend's small verified kernel.
    game = ROOT / "minesweeper"
    run("bend", str(game / "board.bend"), "--check-only")
    board_result = run("bend", str(game / "board4.bend")).splitlines()[-1]
    if board_result != "2":
        raise AssertionError(f"Incorrect full-board clue smoke output: {board_result}")
    run("bend", str(game / "session.bend"), "--check-only")
    engine = run("bend", str(game / "game.bend")).splitlines()[-1]
    if engine != "1":
        raise AssertionError(f"Unexpected visible-state smoke output: {engine}")
    game_verdict = run("bend", str(game / "PROOF.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in game_verdict:
        raise AssertionError(f"Minesweeper law proof gate failed:\n{game_verdict}")
    print("PASS Minesweeper law proof gate (31 laws, including whole-board mine invariants and clues)", flush=True)
    verify_full_neighbor_table(game)
    verify_dense_board(game)
    verify_sessions(game)

    # Mutation test: keeping the function well-typed must not suffice when
    # it violates an independently declared requirement.
    with tempfile.TemporaryDirectory() as td:
        mutant_dir = pathlib.Path(td)
        for name in ("LAWS.bend", "PROOF.bend", "board.bend", "board4.bend"):
            shutil.copyfile(game / name, mutant_dir / name)
        original = (game / "game.bend").read_text(encoding="utf-8")
        mutant = original.replace("    case Hidden{}:\n      Flag{}",
                                  "    case Hidden{}:\n      Hidden{}", 1)
        if mutant == original:
            raise AssertionError("Unable to construct the flagging regression")
        (mutant_dir / "game.bend").write_text(mutant, encoding="utf-8")
        run("bend", str(mutant_dir / "game.bend"), "--check-only")
        rejected = subprocess.run(
            ["bend", str(mutant_dir / "PROOF.bend"), "--verdict"],
            text=True, capture_output=True, timeout=180,
            cwd=ROOT.parent, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        output = rejected.stdout + rejected.stderr
        if "ALL PROOFS CHECK" in output or rejected.returncode == 0:
            raise AssertionError("A well-typed regression incorrectly passed the proof gate:\n" + output)
        print("PASS mutation: invalid flagging implementation rejected by proofs", flush=True)

    nat_verdict = run("bend", str(SAMPLES / "33_nat_induction.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in nat_verdict:
        raise AssertionError(f"Natural-number induction proof failed:\\n{nat_verdict}")
    print("PASS induction law for every Nat", flush=True)
    mask_verdict = run("bend", str(SAMPLES / "34_mine_mask_law.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in mask_verdict:
        raise AssertionError(f"Mine/flag invariants failed: {mask_verdict}")
    print("PASS mine mask unchanged and flag bit changed", flush=True)

    verdict = run("bend", str(SAMPLES / "04_flag_laws.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in verdict:
        raise AssertionError(f"Proof checker did not accept laws:\n{verdict}")
    local_verdict = run("bend", str(SAMPLES / "14_local_inference.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in local_verdict:
        raise AssertionError(f"Local inference proof not accepted:\n{local_verdict}")
    print("PASS local inference law verdict", flush=True)
    result_verdict = run("bend", str(SAMPLES / "22_result_and_game.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in result_verdict:
        raise AssertionError(f"Result-and-game proof not accepted:\n{result_verdict}")
    print("PASS Result-and-game law", flush=True)
    bool_verdict = run("bend", str(SAMPLES / "24_bool_proofs.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in bool_verdict:
        raise AssertionError(f"Boolean law not accepted:\n{bool_verdict}")
    print("PASS universal Boolean law", flush=True)
    print("PASS law verdict", flush=True)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, subprocess.TimeoutExpired, OSError) as exc:
        print("FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
