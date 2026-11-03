#!/usr/bin/env python3
"""Audit a versioned public-only single-clue proof in a separate process.

This verifier imports the replay *checker*, never the certificate generator.
The proof is conditional on the correctness of public clues and initially
certified cells; it is not a global mine-layout satisfiability certificate.
"""
import json
from pathlib import Path
import sys

SOLUTIONS = Path(__file__).resolve().parents[1] / "solutions"
sys.path.insert(0, str(SOLUTIONS))
from nxn_single_clue_checker import Deduction, replay

MAX_BYTES = 65536
FIELDS = {"version", "size", "opened", "certified_mines", "certified_safe", "steps"}
STEP_FIELDS = {"clue", "mines", "safe"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def integer(value, lo, hi, label):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError("invalid " + label)
    return value


def sorted_cells(value, n, label):
    if not isinstance(value, list) or len(value) > n * n:
        raise ValueError("invalid " + label)
    cells = tuple(integer(cell, 0, n*n-1, label) for cell in value)
    if tuple(sorted(set(cells))) != cells:
        raise ValueError("noncanonical " + label)
    return cells


def audit_document(doc):
    if not isinstance(doc, dict) or set(doc) != FIELDS:
        raise ValueError("invalid top-level fields")
    integer(doc["version"], 1, 1, "version")
    n = integer(doc["size"], 2, 100, "size")
    opened = doc["opened"]
    if not isinstance(opened, list) or len(opened) > n*n:
        raise ValueError("invalid opened clues")
    clues = []
    for pair in opened:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("invalid clue pair")
        clues.append((integer(pair[0], 0, n*n-1, "clue cell"),
                      integer(pair[1], 0, 8, "clue number")))
    if tuple(sorted({cell for cell, _ in clues})) != tuple(cell for cell, _ in clues):
        raise ValueError("noncanonical opened clues")
    mines = sorted_cells(doc["certified_mines"], n, "certified_mines")
    safe = sorted_cells(doc["certified_safe"], n, "certified_safe")
    raw_steps = doc["steps"]
    if not isinstance(raw_steps, list) or len(raw_steps) > n*n:
        raise ValueError("invalid step count")
    steps = []
    for step in raw_steps:
        if not isinstance(step, dict) or set(step) != STEP_FIELDS:
            raise ValueError("invalid step fields")
        steps.append(Deduction(
            integer(step["clue"], 0, n*n-1, "step clue"),
            sorted_cells(step["mines"], n, "step mines"),
            sorted_cells(step["safe"], n, "step safe"),
        ))
    result_mines, result_safe = replay(n, tuple(clues), mines, safe, tuple(steps))
    return {"status": "valid", "size": n, "steps": len(steps),
            "mines": list(result_mines), "safe": list(result_safe)}


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: audit_single_clue_witness.py WITNESS.json", file=sys.stderr)
        return 2
    try:
        with open(args[0], "rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("witness exceeds 64 KiB")
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
        result = audit_document(doc)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc)},
                         ensure_ascii=False, sort_keys=True))
        return 3
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
