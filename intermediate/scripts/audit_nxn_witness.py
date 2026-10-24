"""Audit a versioned N x N no-guess witness without importing its generator.

The JSON input can be produced by Python, Bend, or another implementation.
The independent checker is deliberately exponential and bounded.
"""
import argparse
import json
from pathlib import Path

from verify_nxn_certificate import audit

FIELDS = frozenset({"version", "size", "mine_count", "first", "mines",
                    "clicks", "opened_count"})
MAX_BYTES = 65536


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"non-JSON numeric constant: {value}")


def load_witness(path):
    """Load a strict, bounded, versioned certificate; reject ambiguous input."""
    with open(path, "rb") as source:
        raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("witness file too large")
    record = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                        parse_constant=_reject_constant)
    if type(record) is not dict or set(record) != FIELDS:
        raise ValueError("witness fields")
    for field in ("version", "size", "mine_count", "first", "opened_count"):
        if type(record[field]) is not int:
            raise ValueError(f"{field} must be an integer")
    if record["version"] != 1:
        raise ValueError("unsupported witness version")
    for field in ("mines", "clicks"):
        if type(record[field]) is not list or any(type(i) is not int for i in record[field]):
            raise ValueError(f"{field} must be an integer array")
    if len(record["mines"]) != record["mine_count"]:
        raise ValueError("mine count mismatch")
    return record


def verify_file(path, max_hypotheses=100000):
    """Return a JSON-ready audit record; never promote a limit to valid."""
    if type(max_hypotheses) is not int or max_hypotheses < 1:
        raise ValueError("hypothesis limit")
    try:
        witness = load_witness(path)
        result = audit(witness["size"], witness["mines"], witness["first"],
                       witness["clicks"], witness["opened_count"],
                       max_hypotheses=max_hypotheses)
    except (OSError, UnicodeError, ValueError) as exc:
        return {"status": "invalid", "reason": str(exc),
                "checked_clicks": 0, "opened_count": 0}
    return {"status": result.status, "reason": result.reason,
            "checked_clicks": result.checked_clicks,
            "opened_count": result.opened_count,
            "size": witness["size"], "mine_count": witness["mine_count"],
            "first": witness["first"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("witness", type=Path, help="version-1 witness JSON")
    parser.add_argument("--max-hypotheses", type=int, default=100000)
    args = parser.parse_args(argv)
    try:
        record = verify_file(args.witness, args.max_hypotheses)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return {"valid": 0, "limit": 2, "invalid": 3}[record["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
