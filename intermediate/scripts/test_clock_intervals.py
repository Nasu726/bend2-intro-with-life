#!/usr/bin/env python3
"""Chapter 8 real Bend IO.now / IO.sleep regression.

These are finite observations on the CI host, not a timing precision proof.
We verify monotonic timestamps and loose minimum waits, not exact 20/100 ms.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scripts" / "fixtures" / "clock_intervals.bend"


def run(*args: str, source: Path = FIXTURE) -> tuple[subprocess.CompletedProcess[str], float]:
    start = time.monotonic()
    result = subprocess.run(
        ["bend", str(source), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
    )
    wall_ms = (time.monotonic() - start) * 1000
    return result, wall_ms


def verify_exercise_variant(
    name: str, original: str, old_wait: int, new_wait: int,
    expected_waits: tuple[int, int, int],
) -> None:
    """Typecheck and execute a temporary exercise, leaving the learner file intact."""
    anchor = f"Unit <- IO.sleep({old_wait})"
    if original.count(anchor) != 1:
        raise AssertionError(f"{name}: expected one {anchor!r} in the fixture")
    mutated = original.replace(anchor, f"Unit <- IO.sleep({new_wait})", 1)
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / f"{name}.bend"
        source.write_text(mutated, encoding="utf-8")
        typed, _ = run("--check-only", source=source)
        if typed.returncode:
            raise AssertionError(
                f"{name}: Bend typecheck failed:\n{typed.stdout}\n{typed.stderr}"
            )
        result, wall_ms = run(source=source)
        lines = result.stdout.strip().splitlines()
        if result.returncode or len(lines) != 6 or not all(
            value.isascii() and value.isdecimal() for value in lines
        ):
            raise AssertionError(
                f"{name}: expected six Nat readings, got {lines!r}; "
                f"exit={result.returncode}; stderr={result.stderr!r}"
            )
        stamps = [int(value) for value in lines]
        if any(left > right for left, right in zip(stamps, stamps[1:])):
            raise AssertionError(f"{name}: clock moved backwards: {stamps}")
        elapsed = [stamps[1] - stamps[0], stamps[3] - stamps[2],
                   stamps[5] - stamps[4]]
        # A loose CI acceptance threshold, not a portable IO.sleep guarantee.
        lower = [0, expected_waits[1] // 2, expected_waits[2] // 2]
        if any(observed < bound for observed, bound in zip(elapsed, lower)):
            raise AssertionError(
                f"{name}: observed waits {elapsed} below loose bounds {lower}"
            )
        if sum(elapsed) > wall_ms + 1000:
            raise AssertionError(
                f"{name}: Bend durations {elapsed} exceed "
                f"process wall time {wall_ms:.1f}ms"
            )
        print(
            f"PASS {name} typecheck and execution: "
            f"requested={expected_waits} observed={elapsed}",
            flush=True,
        )


def main() -> int:
    if not shutil.which("bend"):
        raise AssertionError("Bend 2 is required for clock verification")
    if not FIXTURE.is_file():
        raise AssertionError(f"Missing Bend fixture: {FIXTURE}")

    typed, _ = run("--check-only")
    if typed.returncode:
        raise AssertionError(f"Clock fixture typecheck failed:\n{typed.stdout}\n{typed.stderr}")
    print("PASS clock fixture typecheck", flush=True)

    for trial in range(3):
        result, wall_ms = run()
        lines = result.stdout.strip().splitlines()
        if result.returncode or len(lines) != 6 or not all(s.isascii() and s.isdecimal() for s in lines):
            raise AssertionError(
                f"trial={trial}: expected six Nat clock readings, "
                f"got {lines!r}; exit={result.returncode}; stderr={result.stderr!r}"
            )
        stamps = [int(s) for s in lines]
        if any(left > right for left, right in zip(stamps, stamps[1:])):
            raise AssertionError(f"trial={trial}: clock moved backwards: {stamps}")
        elapsed = [stamps[1] - stamps[0], stamps[3] - stamps[2],
                   stamps[5] - stamps[4]]
        # Allow substantial scheduling/clock-resolution variation. A request
        # to wait is not an exact-time guarantee; these loose bounds detect
        # a completely ignored sleep in the observed Linux run.
        if elapsed[1] < 10 or elapsed[2] < 50:
            raise AssertionError(f"trial={trial}: sleep appears ignored: {elapsed}")
        if sum(elapsed) > wall_ms + 1000:
            raise AssertionError(
                f"trial={trial}: Bend durations {elapsed} exceed "
                f"process wall time {wall_ms:.1f}ms"
            )
        print(f"PASS clock trial={trial} waits=0/20/100ms observed={elapsed}", flush=True)
    original = FIXTURE.read_text(encoding="utf-8")
    learner = ROOT / "src" / "55_clock_intervals.bend"
    if not learner.is_file() or learner.read_text(encoding="utf-8") != original:
        raise AssertionError("Chapter 8 learner sample and tested fixture diverged")
    for name, old_wait, new_wait, expected_waits in (
        ("sleep_50ms", 20, 50, (0, 50, 100)),
        ("sleep_200ms", 100, 200, (0, 20, 200)),
    ):
        verify_exercise_variant(name, original, old_wait, new_wait, expected_waits)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, OSError, subprocess.TimeoutExpired) as exc:
        print("FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
