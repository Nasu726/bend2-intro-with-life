#!/usr/bin/env python3
"""Real Bend File.read_bytes chunk/EOF/content regression for chapter 7.

Four bounded reads include a final empty EOF read for 0..5 byte files.
For each chunk, an injective base-257 digest checks the ACTUAL returned bytes
and order, rather than just checking lengths or the untouched source file.
These are local regular files, not a short-read guarantee for all streams.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scripts" / "fixtures" / "binary_chunks.bend"
CONTENT_FIXTURE = ROOT / "scripts" / "fixtures" / "binary_chunks_values.bend"

def run(path: Path, cwd: Path, *, check_only: bool = False):
    args = ["bend", str(path)] + (["--check-only"] if check_only else [])
    return subprocess.run(
        args, cwd=cwd, text=True, capture_output=True, timeout=180,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
    )

def digest(chunk: bytes) -> int:
    value = 0
    for byte in chunk:
        value = value * 257 + byte + 1
    return value


def main() -> int:
    if not shutil.which("bend"):
        raise AssertionError("Bend 2 is required for byte-chunk verification")
    if not FIXTURE.is_file():
        raise AssertionError(f"Missing Bend fixture: {FIXTURE}")
    if not CONTENT_FIXTURE.is_file():
        raise AssertionError(f"Missing Bend content fixture: {CONTENT_FIXTURE}")
    with tempfile.TemporaryDirectory() as directory:
        cwd = Path(directory)
        typed = run(FIXTURE, cwd, check_only=True)
        if typed.returncode:
            raise AssertionError(f"Fixture typecheck failed:\n{typed.stdout}\n{typed.stderr}")
        print("PASS byte chunk fixture typecheck", flush=True)
        content_typed = run(CONTENT_FIXTURE, cwd, check_only=True)
        if content_typed.returncode:
            raise AssertionError(
                f"Content fixture typecheck failed:\n{content_typed.stdout}\n{content_typed.stderr}"
            )
        print("PASS byte content fixture typecheck", flush=True)
        file = cwd / "sample_bytes.bin"
        families = (
            bytes([0, 10, 13, 255, 42]),
            bytes([42, 255, 13, 10, 0]),
            bytes([255] * 5),
            bytes([1, 2, 3, 4, 5]),
        )
        cases = 0
        for family in families:
            for length in range(6):
                payload = family[:length]
                file.write_bytes(payload)
                got = run(CONTENT_FIXTURE, cwd)
                chunks = [payload[offset:offset + 2] for offset in (0, 2, 4, 6)]
                if family == families[0]:
                    # The distributed chapter-7 sample must still behave exactly
                    # like the original four-length reader, unchanged in the ZIP.
                    sample = run(FIXTURE, cwd)
                    lengths = [str(len(chunk)) for chunk in chunks]
                    if sample.returncode or sample.stdout.strip().splitlines() != lengths:
                        raise AssertionError(
                            f"Reader sample length regression for {payload.hex()}: "
                            f"{sample.stdout!r} / {sample.stderr!r}"
                        )
                expected = [str(value) for chunk in chunks
                            for value in (len(chunk), digest(chunk))]
                observed = got.stdout.strip().splitlines()
                # The fourth read must return an empty list, including for length=5.
                if chunks[-1] != b"":
                    raise AssertionError(f"length={length}: test did not reach EOF")
                if got.returncode or observed != expected:
                    raise AssertionError(
                        f"length={length}, payload={payload.hex()}: "
                        f"expected {expected}, got {observed}; "
                        f"exit={got.returncode}, stderr={got.stderr!r}"
                    )
                if file.read_bytes() != payload:
                    raise AssertionError(f"length={length}: read unexpectedly modified the file")
                cases += 1
                print(f"PASS byte content length={length} payload={payload.hex()} "
                      f"digests={expected[1::2]}", flush=True)
        assert cases == 24
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
