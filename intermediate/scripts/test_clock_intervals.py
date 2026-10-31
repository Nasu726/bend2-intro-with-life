#!/usr/bin/env python3
"""Chapter 8 real Bend IO.now / IO.sleep regression.

These are finite observations on the CI host, not a timing precision proof.
We verify monotonic timestamps and loose minimum waits, not exact 20/100 ms.
The pure validator is separately regression-tested without Bend.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scripts" / "fixtures" / "clock_intervals.bend"


def run(*args: str) -> tuple[subprocess.CompletedProcess[str], float]:
    start = time.monotonic()
    result = subprocess.run(
        ["bend", str(FIXTURE), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
    )
    wall_ms = (time.monotonic() - start) * 1000
    return result, wall_ms


def validate_readings(lines: list[str], wall_ms: float, trial: int) -> list[int]:
    """Validate six raw Bend timestamps against a monotonic process clock.

    The lower bounds are deliberately loose and specific to the finite CI
    acceptance test. They are not OS-independent sleep guarantees.
    """
    if len(lines) != 6 or not all(s.isascii() and s.isdecimal() for s in lines):
        raise AssertionError(
            f"trial={trial}: expected six ASCII Nat clock readings, got {lines!r}"
        )
    stamps = [int(s) for s in lines]
    if any(left > right for left, right in zip(stamps, stamps[1:])):
        raise AssertionError(f"trial={trial}: clock moved backwards: {stamps}")
    elapsed = [stamps[1] - stamps[0], stamps[3] - stamps[2],
               stamps[5] - stamps[4]]
    # The zero-wait observation has no minimum. In particular, do not require
    # exact equality for any of the three requested sleep durations.
    if elapsed[1] < 10 or elapsed[2] < 50:
        raise AssertionError(f"trial={trial}: sleep appears ignored: {elapsed}")
    if not (0 <= wall_ms < float("inf")) or sum(elapsed) > wall_ms + 1000:
        raise AssertionError(
            f"trial={trial}: Bend durations {elapsed} incompatible with "
            f"process wall time {wall_ms:.1f}ms"
        )
    return elapsed


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
        if result.returncode:
            raise AssertionError(
                f"trial={trial}: Bend exited {result.returncode}; "
                f"stdout={result.stdout!r}; stderr={result.stderr!r}"
            )
        elapsed = validate_readings(lines, wall_ms, trial)
        print(f"PASS clock trial={trial} waits=0/20/100ms observed={elapsed}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, OSError, subprocess.TimeoutExpired) as exc:
        print("FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
