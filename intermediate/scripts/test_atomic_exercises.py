#!/usr/bin/env python3
"""Chapter 19: verify the old/new values of sequential Array.atomic.add.

Finite Bend runs establish return-value semantics for small U32 operands,
not the atomicity of contended shared updates or GPU behavior. Mutations are
written to a temporary directory; the distributed sample remains unchanged.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "51_atomic_counter.bend"
ANCHOR = "Array.atomic.add(Array.new(U32, 1n, 5), 0, 3)"
# name, initial value, increment, old value, value read back from the array
CASES = (
    ("original", 5, 3, 5, 8),
    ("zero_increment", 5, 0, 5, 5),
    ("zero_initial", 0, 7, 0, 7),
    ("both_zero", 0, 0, 0, 0),
    ("nontrivial", 12, 17, 12, 29),
    ("carry_to_hundred", 99, 1, 99, 100),
)


def mutated(source: str, initial: int, increment: int) -> str:
    if source.count(ANCHOR) != 1:
        raise AssertionError("Chapter 19 source anchor changed or is ambiguous")
    if not (0 <= initial <= 100 and 0 <= increment <= 100):
        raise AssertionError("Test operands must stay in the small U32 range")
    return source.replace(
        ANCHOR,
        f"Array.atomic.add(Array.new(U32, 1n, {initial}), 0, {increment})",
        1,
    )


def verify_static(source: str) -> None:
    if "Array.get(U32, array, 0)" not in source:
        raise AssertionError("Must read the updated array separately")
    if "IO.print(U32.show(before))" not in source:
        raise AssertionError("Must print the old value returned by atomic.add")
    if "IO.print(U32.show(after))" not in source:
        raise AssertionError("Must print the value read by Array.get")
    if len(CASES) != len({name for name, *_ in CASES}):
        raise AssertionError("Duplicate case names")
    for name, initial, increment, before, after in CASES:
        if before != initial or after != initial + increment:
            raise AssertionError(f"Bad independent arithmetic oracle: {name}")
        mutated(source, initial, increment)
    print("PASS chapter 19: six distinct, anchored atomic.add variants", flush=True)


def run(path: Path, *, check_only: bool) -> list[str]:
    command = ["bend", str(path)]
    if check_only:
        command.append("--check-only")
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, timeout=180,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
    )
    if result.returncode:
        raise AssertionError(
            f"Bend failed {path.name}, check_only={check_only}: "
            f"{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip().splitlines()



PAIR_SOURCE = ROOT / "scripts" / "fixtures" / "atomic_two_cells.bend"
PAIR_FIRST = "Array.atomic.add(Array.new(U32, 1n, 5), 0, 3)"
PAIR_SECOND = "Array.atomic.add(array, 1, 7)"
# name, initial value of both cells, first increment, second target, second increment,
# expected: first old value, second old value, final cell 0, final cell 1
PAIR_CASES = (
    ("different_cells", 5, 3, 1, 7, (5, 5, 8, 12)),
    ("same_cell", 5, 3, 0, 7, (5, 8, 15, 5)),
    ("zero_second", 5, 3, 1, 0, (5, 5, 8, 5)),
    ("zero_first", 5, 0, 1, 7, (5, 5, 5, 12)),
    ("both_zero", 0, 0, 0, 0, (0, 0, 0, 0)),
    ("nontrivial", 12, 17, 1, 4, (12, 12, 29, 16)),
)


def pair_variant(source: str, initial: int, first: int,
                 second_index: int, second: int) -> str:
    if source.count(PAIR_FIRST) != 1 or source.count(PAIR_SECOND) != 1:
        raise AssertionError("Two-cell fixture anchors changed or are ambiguous")
    if not (0 <= initial <= 100 and 0 <= first <= 100 and
            0 <= second <= 100 and second_index in (0, 1)):
        raise AssertionError("Two-cell test operands must be bounded")
    return (source.replace(
        PAIR_FIRST,
        f"Array.atomic.add(Array.new(U32, 1n, {initial}), 0, {first})",
        1,
    ).replace(
        PAIR_SECOND,
        f"Array.atomic.add(array, {second_index}, {second})",
        1,
    ))


def verify_pair_static(source: str) -> None:
    if source.count("Array.get(U32, array, 0)") != 1:
        raise AssertionError("Must read back cell 0 exactly once")
    if source.count("Array.get(U32, array, 1)") != 1:
        raise AssertionError("Must read back cell 1 exactly once")
    if source.count("IO.print(U32.show(") != 4:
        raise AssertionError("Must print both old values and both final cells")
    if len(PAIR_CASES) != len({name for name, *_ in PAIR_CASES}):
        raise AssertionError("Duplicate two-cell case names")
    for name, initial, first, index, second, expected in PAIR_CASES:
        independent = (
            initial,
            initial + first if index == 0 else initial,
            initial + first + (second if index == 0 else 0),
            initial + (second if index == 1 else 0),
        )
        if expected != independent:
            raise AssertionError(f"Bad independent two-cell oracle: {name}")
        pair_variant(source, initial, first, index, second)
    print("PASS chapter 19: six two-cell sequential variants with independent oracle",
          flush=True)


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    verify_static(source)
    pair_source = PAIR_SOURCE.read_text(encoding="utf-8")
    distributed_pair = ROOT / "src" / "56_atomic_two_cells.bend"
    if distributed_pair.read_bytes() != PAIR_SOURCE.read_bytes():
        raise AssertionError("Distributed chapter 19 sample must equal Bend-verified two-cell fixture")
    verify_pair_static(pair_source)
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_atomic_exercises.py [--static-only]")
    if not shutil.which("bend"):
        raise AssertionError("Bend 2 required for chapter 19 execution")
    with tempfile.TemporaryDirectory(prefix="bend-atomic-exercises-") as td:
        for name, initial, increment, before, after in CASES:
            path = Path(td) / (name + ".bend")
            path.write_text(mutated(source, initial, increment), encoding="utf-8")
            run(path, check_only=True)
            actual = run(path, check_only=False)
            expected = [str(before), str(after)]
            if actual != expected:
                raise AssertionError(f"{name}: expected {expected}, got {actual}")
            print(f"PASS atomic.add {name}: old={before}, new={after}", flush=True)
        for name, initial, first, index, second, expected in PAIR_CASES:
            path = Path(td) / ("two_cells_" + name + ".bend")
            path.write_text(
                pair_variant(pair_source, initial, first, index, second),
                encoding="utf-8",
            )
            run(path, check_only=True)
            actual = run(path, check_only=False)
            if actual != [str(value) for value in expected]:
                raise AssertionError(
                    f"two_cells_{name}: expected {expected}, got {actual}"
                )
            print(f"PASS two-cell atomic.add {name}: {expected}", flush=True)
    print("PASS twelve chapter 19 variants typechecked and executed", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, subprocess.TimeoutExpired) as exc:
        print("FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
