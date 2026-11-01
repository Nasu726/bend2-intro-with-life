#!/usr/bin/env python3
"""Emit a versioned, public-only single-clue proof for independent replay.

Python reference producer; NOT a Bend N x N solver or no-guess generator.
The separate audit_single_clue_witness.py process is the acceptance gate.
"""
import json
from pathlib import Path
import sys

SOLUTIONS = Path(__file__).resolve().parents[1] / "solutions"
sys.path.insert(0, str(SOLUTIONS))
from nxn_single_clue_certificate import certify
from audit_single_clue_witness import (
    MAX_BYTES, FIELDS, audit_document, integer, sorted_cells, unique_object,
)

INPUT_FIELDS = FIELDS - {"steps"}


def produce(doc):
    """Turn canonical public evidence into a complete replayable witness."""
    if not isinstance(doc, dict) or set(doc) != INPUT_FIELDS:
        raise ValueError("invalid input fields")
    integer(doc["version"], 1, 1, "version")
    n = integer(doc["size"], 2, 100, "size")
    raw_clues = doc["opened"]
    if not isinstance(raw_clues, list) or len(raw_clues) > n*n:
        raise ValueError("invalid opened clues")
    clues = []
    for pair in raw_clues:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("invalid clue pair")
        clues.append((integer(pair[0], 0, n*n-1, "clue cell"),
                      integer(pair[1], 0, 8, "clue number")))
    if tuple(sorted({cell for cell, _ in clues})) != tuple(cell for cell, _ in clues):
        raise ValueError("noncanonical opened clues")
    mines = sorted_cells(doc["certified_mines"], n, "certified_mines")
    safe = sorted_cells(doc["certified_safe"], n, "certified_safe")
    _, _, proof = certify(n, clues, mines, safe)
    witness = {**doc, "steps": [{"clue": step.clue, "mines": list(step.mines),
                              "safe": list(step.safe)} for step in proof]}
    audit_document(witness)
    return witness


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: emit_single_clue_witness.py PUBLIC.json WITNESS.json",
              file=sys.stderr)
        return 2
    try:
        with open(args[0], "rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("public evidence exceeds 64 KiB")
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
        witness = produce(doc)
        encoded = (json.dumps(witness, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")) + "\n").encode("utf-8")
        if len(encoded) > MAX_BYTES:
            raise ValueError("generated witness exceeds 64 KiB")
        # Do not overwrite a reader's input or an existing proof.
        with open(args[1], "xb") as output:
            output.write(encoded)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc)},
                         ensure_ascii=False, sort_keys=True))
        return 3
    print(json.dumps({"status": "written", "steps": len(witness["steps"]),
                      "path": str(Path(args[1]))}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
