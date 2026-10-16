#!/usr/bin/env python3
"""Bend integration tests: typecheck and execute; any mismatch exits nonzero.

These are *not* print-only smoke tests. They use the actual Bend compiler
and validate the process return code and calculated values. Requires `bend`.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
FAILURE_SOURCE = SOURCE / "12_affine_probe_INVALID.bend"


def run(args: list[str], timeout: int = 120) -> str:
    env = dict(os.environ, BEND_NO_TELEMETRY="1")
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True,
                          env=env, timeout=timeout)
    if proc.returncode != 0:
        raise AssertionError(
            f"Command failed (exit {proc.returncode}): {args!r}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout.replace("\r\n", "\n")


def test_all_sources() -> None:
    sources = sorted(SOURCE.glob("*.bend"))
    assert sources, "No Bend examples found"
    errors = []
    for src in sources:
        if src == FAILURE_SOURCE:
            continue
        print(f"TYPECHECK {src.relative_to(ROOT)}", flush=True)
        try:
            run(["bend", str(src), "--check-only"])
        except AssertionError as exc:
            errors.append(str(exc))
    if errors:
        raise AssertionError("\n\n".join(errors))
    print(f"PASS: {len(sources)-1} source files typechecked")


def test_expected_failure() -> None:
    assert FAILURE_SOURCE.exists()
    proc = subprocess.run(["bend", str(FAILURE_SOURCE), "--check-only"],
                          cwd=ROOT, text=True, capture_output=True,
                          env=dict(os.environ, BEND_NO_TELEMETRY="1"), timeout=120)
    if proc.returncode == 0:
        raise AssertionError("INVALID example unexpectedly passed typechecking")
    print("PASS: intentional ownership error rejected")


def test_rule_table() -> None:
    """Run all 18 valid cell/current-neighbour combinations in Bend itself."""
    original = (SOURCE / "03_rule.bend").read_text(encoding="utf-8")
    head, separator, _old_main = original.partition("def main() -> U32:")
    assert separator, "The rule example's main signature changed: update this harness"
    cases = [(live, neighbours) for live in (0, 1) for neighbours in range(9)]
    program = head + "\ndef main() -> IO(Unit):\n  do IO<Unit>:\n"
    program += '    IO.print("RULE_TEST_BEGIN")\n'
    program += "".join(f"    IO.print(U32.show(rule({alive}, {n})))\n"
                       for alive, n in cases)
    program += '    IO.print("RULE_TEST_END")\n'
    expected = [str(int(n == 3 or (n == 2 and live == 1))) for live, n in cases]
    with tempfile.TemporaryDirectory(prefix="bend-life-rules-") as td:
        p = Path(td) / "rules.bend"
        p.write_text(program, encoding="utf-8")
        actual = run(["bend", str(p)])
    begin = actual.find("RULE_TEST_BEGIN\n")
    end = actual.find("RULE_TEST_END\n", begin + 1)
    if begin == -1 or end == -1:
        raise AssertionError("Rule test markers missing from Bend output:\n" + actual)
    inside = actual[begin + len("RULE_TEST_BEGIN\n"):end].splitlines()
    if inside != expected:
        raise AssertionError("Incorrect Bend rule table:\n"
                             f"expected: {expected}\nactual: {inside}")
    print("PASS: 18/18 combinations of alive and neighbours")


def test_life_transcript() -> None:
    # Importing the oracle only supplies the expected output. It does not
    # replace running the Bend code, and mismatches raise an AssertionError.
    sys.path.insert(0, str(ROOT / "scripts"))
    from reference import transcript

    actual = run(["bend", str(SOURCE / "08_life_terminal.bend")])
    begin = actual.find("generation 0\n")
    end = actual.find("done\n", begin + 1)
    if begin < 0 or end < 0:
        raise AssertionError("Life transcript markers missing:\n" + actual)
    observed = actual[begin:end+len("done\n")]
    expected = transcript()
    if observed != expected:
        import difflib
        delta = "".join(difflib.unified_diff(expected.splitlines(True),
                                              observed.splitlines(True),
                                              fromfile="Python oracle",
                                              tofile="Bend terminal"))
        raise AssertionError("Bend life state differs from oracle:\n" + delta)
    print("PASS: complete five-generation board transcript")



def test_higher_order_result() -> None:
    """Check actual output, not just the function's type."""
    actual = run(["bend", str(SOURCE / "29_higher_order.bend")]).strip()
    if actual.splitlines()[-1] != "42":
        raise AssertionError(f"Higher-order function expected 42, got {actual!r}")
    print("PASS: higher-order apply(lambda, 40) = 42")


def test_monad_bind_equivalence() -> None:
    """Both do-notation and explicit bind handle success and failure alike."""
    for path, fn in (("21_monadic_maybe.bend", "add_strs"),
                     ("30_monad_explicit.bend", "add_strs_explicit")):
        original = (SOURCE / path).read_text(encoding="utf-8")
        head, separator, _main = original.partition("def main() ->")
        if not separator:
            raise AssertionError(f"Missing main definition in {path}")
        for a, b, expected in (("40", "2", 42), ("bad", "2", 999)):
            program = (head + "def main() -> U32:\n"
                       + f'  Maybe.default(&2, U32, {fn}("{a}", "{b}"), 999)\n')
            with tempfile.TemporaryDirectory(prefix="bend-monad-") as td:
                tmp = Path(td) / "main.bend"
                tmp.write_text(program, encoding="utf-8")
                observed = run(["bend", str(tmp)]).strip()
            if observed.splitlines()[-1] != str(expected):
                raise AssertionError(f"{path}({a!r},{b!r}) expected {expected}, got {observed!r}")
    print("PASS: do and explicit bind match on success and failure")



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-typecheck", action="store_true")
    args = parser.parse_args()
    if shutil.which("bend") is None:
        print("ERROR: Bend is not installed; tests must not silently skip", file=sys.stderr)
        return 2
    print("Installed Bend:", run(["bend", "version"]).strip(), flush=True)
    tests = [test_rule_table, test_life_transcript, test_higher_order_result, test_monad_bind_equivalence]
    if not args.no_typecheck:
        tests[:0] = [test_all_sources, test_expected_failure]
    errors = []
    for test in tests:
        try:
            test()
        except (AssertionError, OSError, subprocess.TimeoutExpired) as exc:
            print(f"FAIL {test.__name__}: {exc}", file=sys.stderr)
            errors.append(test.__name__)
    if errors:
        print(f"FAILED: {len(errors)} tests: {', '.join(errors)}", file=sys.stderr)
        return 1
    print(f"PASS: {len(tests)} Bend integration checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
