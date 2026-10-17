#!/usr/bin/env python3
"""Compile one IO sample to native C and JavaScript and execute both targets.

This integration test intentionally tests the emitted programs, not just that
Bend wrote C/JS files. GUI/GPU/FFI behavior is not covered by this test.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "43_target_hello.bend"

def run(*argv):
    result = subprocess.run(argv, cwd=ROOT.parent, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
                            capture_output=True, text=True, timeout=240)
    if result.returncode:
        raise AssertionError(
            f"Command {argv!r} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()

def main():
    for tool in ("bend", "node", "clang"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} is required for target tests")
    expected = run("bend", str(SOURCE))
    if expected != "42":
        raise AssertionError(f"Unexpected Bend output: {expected!r}")
    with tempfile.TemporaryDirectory(prefix="bend-targets-") as tmp:
        out = Path(tmp)
        c_source = out / "hello.c"
        native = out / "hello"
        js = out / "hello.js"
        run("bend", str(SOURCE), "-o", str(c_source))
        if c_source.stat().st_size < 100:
            raise AssertionError("C source was not generated")
        run("bend", str(SOURCE), "-o", str(native))
        native_output = run(str(native))
        if native_output != expected:
            raise AssertionError(f"Native C output {native_output!r} differs from {expected!r}")
        run("bend", str(SOURCE), "-o", str(js))
        if js.stat().st_size < 100:
            raise AssertionError("JavaScript was not generated")
        run("node", "--check", str(js))
        javascript_output = run("node", str(js))
        if javascript_output != expected:
            raise AssertionError(f"Node output {javascript_output!r} differs from {expected!r}")
        print("PASS C source emission, native compile+run, and Node JS execution: all print 42")

if __name__ == "__main__":
    main()
