#!/usr/bin/env python3
"""Real Bend File.read_bytes chunk/EOF/content regression for chapter 7.

Four reads observe EOF for 0..6-byte regular files; five reads do so for
0..8 bytes. Equal observed prefixes (8/9 and 10/11) show why neither
fixed read count establishes EOF for arbitrary file sizes.
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


def length_from_digest(value: int) -> int:
    """Independent oracle for the <=2-byte digest length intervals."""
    if value == 0:
        return 0
    if 1 <= value <= 256:
        return 1
    if 258 <= value <= 66048:
        return 2
    raise AssertionError(f"Out-of-range <=2-byte fingerprint: {value}")


def verify_fingerprint() -> None:
    """Prove injectivity over all 0-, 1-, and 2-byte sequences."""
    observed = {0}
    for b in range(256):
        fingerprint = digest(bytes((b,)))
        if fingerprint in observed or length_from_digest(fingerprint) != 1:
            raise AssertionError("1-byte digest collision or length error")
        observed.add(fingerprint)
    for left in range(256):
        for right in range(256):
            fingerprint = digest(bytes((left, right)))
            if fingerprint in observed or length_from_digest(fingerprint) != 2:
                raise AssertionError("2-byte digest collision or length error")
            observed.add(fingerprint)
    if len(observed) != 1 + 256 + 65536:
        raise AssertionError("Unexpected fingerprint cardinality")
    print("PASS exhaustive 65,793 fingerprints (length <= 2)", flush=True)


def main() -> int:
    verify_fingerprint()
    fixture_source = CONTENT_FIXTURE.read_text(encoding="utf-8")
    chunk_body = fixture_source.split("def report_chunk(", 1)[1].split(
        "\ndef after_fifth(", 1
    )[0]
    # Bend IO/do expects monadic patterns. Pure shared lets must precede it.
    if not (chunk_body.index("+digest =") < chunk_body.index("+length =")
            < chunk_body.index("do IO<Unit>:")):
        raise AssertionError("Pure shared lets were placed inside do IO")
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
            bytes([0, 10, 13, 255, 42, 0, 7, 8, 9, 10, 11]),
            bytes([42, 255, 13, 10, 0, 7, 8, 9, 10, 11, 12]),
            bytes([255] * 11),
            bytes(range(1, 12)),
        )
        cases = 0
        for family in families:
            prefix_observations = {}
            for length in range(12):
                payload = family[:length]
                file.write_bytes(payload)
                got = run(CONTENT_FIXTURE, cwd)
                chunks = [payload[offset:offset + 2] for offset in (0, 2, 4, 6, 8)]
                if family == families[0]:
                    # The distributed chapter-7 sample must still behave exactly
                    # like the original four-length reader, unchanged in the ZIP.
                    sample = run(FIXTURE, cwd)
                    lengths = [str(len(chunk)) for chunk in chunks[:4]]
                    if sample.returncode or sample.stdout.strip().splitlines() != lengths:
                        raise AssertionError(
                            f"Reader sample length regression for {payload.hex()}: "
                            f"{sample.stdout!r} / {sample.stderr!r}"
                        )
                for chunk in chunks:
                    if length_from_digest(digest(chunk)) != len(chunk):
                        raise AssertionError("Fingerprint cannot recover bounded chunk length")
                expected = [str(value) for chunk in chunks
                            for value in (len(chunk), digest(chunk))]
                observed = got.stdout.strip().splitlines()
                # A zero-length read, not a fixed number of calls, observes EOF.
                # Four calls can consume at most eight bytes; five at most ten.
                if (len(chunks[3]) == 0) != (length <= 6):
                    raise AssertionError(
                        f"length={length}: fourth-read EOF expectation is wrong")
                if (len(chunks[4]) == 0) != (length <= 8):
                    raise AssertionError(
                        f"length={length}: fifth-read EOF expectation is wrong")
                if got.returncode or observed != expected:
                    raise AssertionError(
                        f"length={length}, payload={payload.hex()}: "
                        f"expected {expected}, got {observed}; "
                        f"exit={got.returncode}, stderr={got.stderr!r}"
                    )
                if file.read_bytes() != payload:
                    raise AssertionError(f"length={length}: read unexpectedly modified the file")
                cases += 1
                if length in (8, 9, 10, 11):
                    prefix_observations[length] = observed
                print(f"PASS byte content length={length} payload={payload.hex()} "
                      f"digests={expected[1::2]}", flush=True)
            if prefix_observations[8][:8] != prefix_observations[9][:8]:
                raise AssertionError(
                    "Four bounded reads must not distinguish 8 from 9 bytes "
                    "when the first eight bytes are identical")
            if prefix_observations[8] == prefix_observations[9]:
                raise AssertionError(
                    "Fifth read must distinguish 8 from 9 bytes by observing EOF")
            if prefix_observations[10] != prefix_observations[11]:
                raise AssertionError(
                    "Five bounded reads must not distinguish 10 from 11 bytes "
                    "when the first ten bytes are identical")
        assert cases == 48
        print("PASS 48 byte-content cases; fourth-read EOF for 0..6, "
              "fifth-read EOF for 0..8", flush=True)
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
