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
    engine = run("bend", str(game / "game.bend")).splitlines()[-1]
    if engine != "1":
        raise AssertionError(f"Unexpected visible-state smoke output: {engine}")
    game_verdict = run("bend", str(game / "PROOF.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in game_verdict:
        raise AssertionError(f"Minesweeper law proof gate failed:\n{game_verdict}")
    print("PASS Minesweeper law proof gate (22 laws, including whole-board mine invariants and clues)", flush=True)
    verify_full_neighbor_table(game)

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
