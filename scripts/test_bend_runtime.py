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
    """A higher-order function must execute the supplied function."""
    actual = run(["bend", str(SOURCE / "29_higher_order.bend")]).strip()
    if actual.splitlines()[-1] != "42":
        raise AssertionError(f"Higher-order function expected 42, got {actual!r}")
    print("PASS: high-order apply(lambda, 40) = 42")


def test_monad_bind_equivalence() -> None:
    """Compare do and explicit bind with both success and failure cases."""
    for path, fn in (("21_monadic_maybe.bend", "add_strs"),
                     ("30_monad_explicit.bend", "add_strs_explicit")):
        original = (SOURCE / path).read_text(encoding="utf-8")
        head, sep, _ = original.partition("def main() ->")
        if not sep:
            raise AssertionError(f"No main found in {path}")
        for a, b, expected in (("40", "2", 42), ("bad", "2", 999)):
            program = head + (
                "def main() -> U32:\n"
                f'  Maybe.default(&2, U32, {fn}("{a}", "{b}"), 999)\n'
            )
            with tempfile.TemporaryDirectory(prefix="bend-monad-") as td:
                temporary = Path(td) / "main.bend"
                temporary.write_text(program, encoding="utf-8")
                got = run(["bend", str(temporary)]).strip()
            if got.splitlines()[-1] != str(expected):
                raise AssertionError(
                    f"{path}({a!r},{b!r}) expected {expected}, got {got!r}"
                )
    print("PASS: do and explicit bind agree on success and failure")

def test_xy_index_mapping() -> None:
    """Execute the helper in real Bend, including row boundary cases."""
    original = (SOURCE / "05_glider.bend").read_text(encoding="utf8")
    head, marker, unused_main = original.partition("def main() -> U32:")
    assert marker
    coords = [(0, 0), (7, 0), (0, 1), (3, 2), (7, 7)]
    program = head + "\ndef main() -> IO(Unit):\n  do IO<Unit>:\n"
    for x,y in coords:
        program += f'    IO.print(U32.show(index({x}, {y})))\n'
    with tempfile.TemporaryDirectory(prefix="bend-xy-index-") as td:
        temp=Path(td)/"coordinates.bend"
        temp.write_text(program,encoding="utf8")
        actual=run(["bend",str(temp)]).strip().splitlines()
    assert actual == ["0","7","8","19","63"], actual
    print("PASS 8x8 index(x,y) = 0,7,8,19,63")

def test_parallel_and_proofs() -> None:
    expected_results = (("09_parallel_tree.bend", "4096"),
                        ("10_gpu_tree.bend", "4096"),
                        ("31_parallel_life_pair.bend", "2"),
                        ("32_gpu_life_call.bend", "1"))
    for name, expected in expected_results:
        got = run(["bend", str(SOURCE / name)], timeout=180).strip().splitlines()[-1]
        if got != expected:
            raise AssertionError(f"{name}: expected {expected}, got {got}")
    for name in ("11_rule_proofs.bend", "24_proof_induction.bend"):
        out = run(["bend", str(SOURCE / name), "--verdict"], timeout=180)
        if "ALL PROOFS CHECK" not in out:
            raise AssertionError(f"Proof verdict did not certify {name}:\n{out}")
    print("PASS: CPU/GPU-call syntax and verified laws and induction")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-typecheck", action="store_true")
    args = parser.parse_args()
    if shutil.which("bend") is None:
        print("ERROR: Bend is not installed; tests must not silently skip", file=sys.stderr)
        return 2
    print("Installed Bend:", run(["bend", "version"]).strip(), flush=True)
    tests = [test_rule_table, test_xy_index_mapping, test_life_transcript, test_higher_order_result, test_monad_bind_equivalence, test_parallel_and_proofs]
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
