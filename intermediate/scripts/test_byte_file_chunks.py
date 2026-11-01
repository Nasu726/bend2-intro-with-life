#!/usr/bin/env python3
"""Real Bend File.read_bytes chunk/EOF/content regression for chapter 7.

Four reads observe EOF for 0..6-byte regular files; five for 0..8 and
six for 0..10. Equal prefixes (8/9, 10/11, 12/13) show why no fixed
read count establishes EOF for arbitrary file sizes.
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



def parse_stdout_lines(stdout: str) -> list[str]:
    """Preserve blank lines and padding, allowing at most one terminal LF.

    subprocess(text=True) normalizes CRLF to LF before this function.
    """
    if not isinstance(stdout, str):
        raise AssertionError(f"Expected text stdout, got {type(stdout).__name__}")
    lines = stdout.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines

def validate_chunk_output(payload: bytes, lines: list[str], *, reads: int = 6) -> None:
    """Compare bounded File.read_bytes output with an independent byte oracle.

    Each read reports two canonical decimal lines: actual length, base-257
    fingerprint. This finite oracle assumes a regular file read in 2-byte
    chunks, as exercised by the chapter-7 Bend fixture; it is not a stream
    short-read guarantee.
    """
    if reads < 1:
        raise ValueError("reads must be positive")
    if len(lines) != 2 * reads or any(
        not isinstance(line, str) or not line.isascii() or not line.isdecimal() or len(line) > 5
        or (len(line) > 1 and line[0] == "0")
        for line in lines
    ):
        raise AssertionError(f"Expected {2 * reads} canonical decimal lines, got {lines!r}")
    chunks = [payload[offset:offset + 2] for offset in range(0, 2 * reads, 2)]
    expected = [value for chunk in chunks for value in (len(chunk), digest(chunk))]
    observed = [int(line) for line in lines]
    if observed != expected:
        raise AssertionError(f"Expected {expected}, got {observed}")


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
        "\ndef after_sixth(", 1
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
            bytes([0, 10, 13, 255, 42, 0, 7, 8, 9, 10, 11, 12, 13]),
            bytes([42, 255, 13, 10, 0, 7, 8, 9, 10, 11, 12, 13, 14]),
            bytes([255] * 13),
            bytes(range(1, 14)),
        )
        cases = 0
        for family in families:
            prefix_observations = {}
            for length in range(14):
                payload = family[:length]
                file.write_bytes(payload)
                got = run(CONTENT_FIXTURE, cwd)
                chunks = [payload[offset:offset + 2] for offset in (0, 2, 4, 6, 8, 10)]
                if family == families[0]:
                    # The distributed chapter-7 sample must still behave exactly
                    # like the original four-length reader, unchanged in the ZIP.
                    sample = run(FIXTURE, cwd)
                    lengths = [str(len(chunk)) for chunk in chunks[:4]]
                    if sample.returncode or parse_stdout_lines(sample.stdout) != lengths:
                        raise AssertionError(
                            f"Reader sample length regression for {payload.hex()}: "
                            f"{sample.stdout!r} / {sample.stderr!r}"
                        )
                for chunk in chunks:
                    if length_from_digest(digest(chunk)) != len(chunk):
                        raise AssertionError("Fingerprint cannot recover bounded chunk length")
                expected = [str(value) for chunk in chunks
                            for value in (len(chunk), digest(chunk))]
                observed = parse_stdout_lines(got.stdout)
                # A zero-length read, not a fixed number of calls, observes EOF.
                # Four/five/six calls can consume at most 8/10/12 bytes.
                if (len(chunks[3]) == 0) != (length <= 6):
                    raise AssertionError(
                        f"length={length}: fourth-read EOF expectation is wrong")
                if (len(chunks[4]) == 0) != (length <= 8):
                    raise AssertionError(
                        f"length={length}: fifth-read EOF expectation is wrong")
                if (len(chunks[5]) == 0) != (length <= 10):
                    raise AssertionError(
                        f"length={length}: sixth-read EOF expectation is wrong")
                if got.returncode:
                    raise AssertionError(
                        f"length={length}, payload={payload.hex()}: "
                        f"Bend exited {got.returncode}; stderr={got.stderr!r}"
                    )
                try:
                    validate_chunk_output(payload, observed)
                except AssertionError as exc:
                    raise AssertionError(
                        f"length={length}, payload={payload.hex()}: {exc}; "
                        f"stderr={got.stderr!r}"
                    ) from exc
                if file.read_bytes() != payload:
                    raise AssertionError(f"length={length}: read unexpectedly modified the file")
                cases += 1
                if length in (8, 9, 10, 11, 12, 13):
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
            if prefix_observations[10][:10] != prefix_observations[11][:10]:
                raise AssertionError(
                    "Five bounded reads must not distinguish 10 from 11 bytes "
                    "when the first ten bytes are identical")
            if prefix_observations[10] == prefix_observations[11]:
                raise AssertionError(
                    "Sixth read must distinguish 10 from 11 bytes by observing EOF")
            if prefix_observations[12] != prefix_observations[13]:
                raise AssertionError(
                    "Six bounded reads must not distinguish 12 from 13 bytes "
                    "when the first twelve bytes are identical")
        assert cases == 56
        print("PASS 56 byte-content cases; fourth-read EOF for 0..6, "
              "fifth-read EOF for 0..8, sixth-read EOF for 0..10", flush=True)
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
