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


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    verify_static(source)
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
    print("PASS six chapter 19 variants typechecked and executed", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, subprocess.TimeoutExpired) as exc:
        print("FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
