#!/usr/bin/env python3
"""Exercise mutations for textbook chapters 3-4, verified with Bend 2.

The original 14 examples are already covered by test_examples.py. These
mutations verify the *predicted results* of selected reader exercises, without
changing the distributed sample files. Finite tests, not API proofs.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from test_examples import EXPECTED

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "src"
TEX = ROOT / "Intermediate_Textbook.tex"

CHAPTER_SAMPLES = {
    3: (
        "03_list.bend", "40_list_map.bend", "17_list_pipeline.bend",
        "38_list_sort.bend", "18_array_mutations.bend",
        "39_array_to_list.bend", "30_array_clone.bend",
    ),
    4: (
        "01_set.bend", "05_marking.bend", "02_map.bend",
        "36_map_missing.bend", "16_map_set_api.bend",
        "49_map_update_delete.bend", "50_set_from_list.bend",
    ),
}

# name, sample, exact original snippet, exact replacement, expected stdout
VARIANTS = (
    ("map_plus_two", "40_list_map.bend",
     "(x + 1 : U32)", "(x + 2 : U32)", "12"),
    ("filter_below_two", "17_list_pipeline.bend",
     "Nat.is_lt(n, 3n)", "Nat.is_lt(n, 2n)", "1n"),
    ("fold_initial_five", "17_list_pipeline.bend",
     "~sum, ys, 0n)", "~sum, ys, 5n)", "8n"),
    ("sort_descending", "38_list_sort.bend",
     "~U32.is_le", "~U32.is_ge", "7"),
    ("wins_twelve", "49_map_update_delete.bend",
     'm3 = Map.set(&2, U32, m2, "wins", 8)',
     'm3 = Map.set(&2, U32, m2, "wins", 12)', "13"),
    ("delete_missing_key", "49_map_update_delete.bend",
     'Map.del(&2, U32, m3, "games")',
     'Map.del(&2, U32, m3, "not-found")', "11"),
    ("registered_zero", "36_map_missing.bend",
     '  count_first(Map.has(&2, U32, m1, "wins"))',
     '  m2 = Map.set(&2, U32, m1, "losses", 0)\n'
     '  count_first(Map.has(&2, U32, m2, "wins"))', "2"),
    ("delete_existing_set_key", "50_set_from_list.bend",
     'Set.del(s0, "3,3")', 'Set.del(s0, "1,1")', "1n"),
    ("append_distinct_set_key", "50_set_from_list.bend",
     '["0,0", "1,1", "0,0"]',
     '["0,0", "1,1", "0,0", "2,2"]', "3n"),
    ("keep_set_key", "16_map_set_api.bend",
     'Set.del(s3, "0,0")',
     'Set.del(s3, "not-found")', "4n"),
)


def changed_source(sample, before, after):
    source = (SAMPLES / sample).read_text(encoding="utf-8")
    if before == after or source.count(before) != 1:
        raise AssertionError(
            f"{sample}: expected one unique mutation anchor {before!r}"
        )
    return source.replace(before, after, 1)


def verify_static():
    tex = TEX.read_text(encoding="utf-8")
    headers = list(re.finditer(r"^\\chapter\{[^}\n]+\}", tex, re.MULTILINE))
    if len(headers) != 23:
        raise AssertionError(f"Expected 23 chapters, got {len(headers)}")
    for number, expected in CHAPTER_SAMPLES.items():
        start = headers[number - 1].end()
        end = headers[number].start()
        body = tex[start:end]
        actual = tuple(re.findall(r"\\sample\{([^}]+)\}", body))
        if actual != expected:
            raise AssertionError(
                f"Chapter {number} sample references changed: {actual}"
            )
        for sample in expected:
            if sample not in EXPECTED or not (SAMPLES / sample).is_file():
                raise AssertionError(
                    f"Chapter {number}: untested or missing sample {sample}"
                )
        if r"\exercise{" not in body:
            raise AssertionError(f"Chapter {number} lost its exercises")
    if len(VARIANTS) != 10 or len({v[0] for v in VARIANTS}) != len(VARIANTS):
        raise AssertionError("Exercise variants must be 10 unique cases")
    for name, sample, before, after, expected in VARIANTS:
        if sample not in CHAPTER_SAMPLES[3] + CHAPTER_SAMPLES[4]:
            raise AssertionError(f"{name}: not a chapter 3-4 sample")
        if not expected:
            raise AssertionError(f"{name}: empty expected output")
        changed_source(sample, before, after)
    print("PASS 14 original chapter 3-4 samples have runtime expectations; "
          "10 exercise mutations have unique anchors", flush=True)


def run_bend(command, source, name):
    try:
        p = subprocess.run(
            ["bend", str(source), *command],
            cwd=ROOT.parent, text=True, capture_output=True, timeout=120,
            env=dict(os.environ, BEND_NO_TELEMETRY="1"),
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"{name}: Bend timeout: {command}") from exc
    if p.returncode:
        raise AssertionError(
            f"{name}: Bend {command} failed\n{p.stdout}\n{p.stderr}"
        )
    return p.stdout.strip().splitlines()


def main():
    verify_static()
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_collection_exercises.py [--static-only]")
    with tempfile.TemporaryDirectory() as tmp:
        for name, sample, before, after, expected in VARIANTS:
            path = Path(tmp) / (name + ".bend")
            path.write_text(changed_source(sample, before, after),
                            encoding="utf-8")
            run_bend(["--check-only"], path, name)
            output = run_bend([], path, name)
            if not output or output[-1] != expected:
                raise AssertionError(
                    f"{name}: expected {expected!r}, got {output!r}"
                )
            print(f"PASS {name}: {expected}", flush=True)
    print("PASS 10 chapter 3-4 exercise mutations typechecked and executed",
          flush=True)


if __name__ == "__main__":
    main()
