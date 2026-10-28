#!/usr/bin/env python3
"""Real Bend File.read_bytes chunk/EOF regression for chapter 7.

Four bounded reads ensure that even a five-byte file reaches an empty EOF
read. The 0..5 byte inputs are local regular files, not a general short-read
guarantee for pipes, sockets, or all operating systems.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scripts" / "fixtures" / "binary_chunks.bend"

def run(path: Path, cwd: Path, *, check_only: bool = False):
    args = ["bend", str(path)] + (["--check-only"] if check_only else [])
    return subprocess.run(
        args, cwd=cwd, text=True, capture_output=True, timeout=180,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
    )

def main() -> int:
    if not shutil.which("bend"):
        raise AssertionError("Bend 2 is required for byte-chunk verification")
    if not FIXTURE.is_file():
        raise AssertionError(f"Missing Bend fixture: {FIXTURE}")
    with tempfile.TemporaryDirectory() as directory:
        cwd = Path(directory)
        typed = run(FIXTURE, cwd, check_only=True)
        if typed.returncode:
            raise AssertionError(f"Fixture typecheck failed:\n{typed.stdout}\n{typed.stderr}")
        print("PASS byte chunk fixture typecheck", flush=True)
        file = cwd / "sample_bytes.bin"
        for length in range(6):
            payload = bytes([0, 10, 13, 255, 42][:length])
            file.write_bytes(payload)
            got = run(FIXTURE, cwd)
            expected = [min(2, max(0, length - offset)) for offset in (0, 2, 4, 6)]
            observed = got.stdout.strip().splitlines()
            # The fourth read must return an empty list, including for length=5.
            if expected[-1] != 0:
                raise AssertionError(f"length={length}: test did not reach EOF")
            if got.returncode or observed != [str(n) for n in expected]:
                raise AssertionError(
                    f"length={length}: expected {expected}, got {observed}; "
                    f"exit={got.returncode}, stderr={got.stderr!r}"
                )
            if file.read_bytes() != payload:
                raise AssertionError(f"length={length}: read unexpectedly modified the file")
            print(f"PASS byte chunks length={length}: {expected}", flush=True)
        file.unlink()
        missing = run(FIXTURE, cwd)
        if missing.returncode == 0:
            raise AssertionError("Missing binary file was treated as a successful read")
        print("PASS missing binary file rejected", flush=True)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, OSError, subprocess.TimeoutExpired) as exc:
        print("FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
