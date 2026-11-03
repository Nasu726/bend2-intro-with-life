"""Generate and independently audit an N x N no-guess candidate.

This is a Python reference pipeline, not the general-size Bend implementation.
The generator uses a frontier solver; the independent auditor enumerates full
mine placements. An auditor limit is never reported as a verified witness.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
from nxn_candidate_generator import generate
from verify_nxn_certificate import audit


def run(n=4, mine_count=2, first=0, max_candidates=120,
        max_frontier=18, max_hypotheses=100000):
    """Return a JSON-ready record with separate generation/audit outcomes."""
    result = generate(n, mine_count, first, max_candidates=max_candidates,
                      max_frontier=max_frontier)
    record = {
        "status": result.status,
        "generation_status": result.status,
        "size": n,
        "mine_count": mine_count,
        "first": first,
        "examined": result.examined,
        "possible": result.possible,
        "stuck": result.stuck,
        "limited": result.limited,
    }
    if result.certificate is None:
        return record

    certificate = result.certificate
    record.update(mines=list(certificate.mines), clicks=list(certificate.clicks),
                  opened_count=certificate.opened_count)
    check = audit(n, certificate.mines, first, certificate.clicks,
                  certificate.opened_count, max_hypotheses=max_hypotheses)
    record.update(audit_status=check.status,
                  audit_checked_clicks=check.checked_clicks,
                  audit_opened_count=check.opened_count,
                  audit_reason=check.reason)
    record["status"] = {"valid": "verified", "limit": "audit_limit",
                        "invalid": "audit_invalid"}[check.status]
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=4)
    parser.add_argument("--mine-count", type=int, default=2)
    parser.add_argument("--first", type=int, default=0)
    parser.add_argument("--max-candidates", type=int, default=120)
    parser.add_argument("--max-frontier", type=int, default=18)
    parser.add_argument("--max-hypotheses", type=int, default=100000)
    args = parser.parse_args(argv)
    try:
        record = run(args.size, args.mine_count, args.first,
                     args.max_candidates, args.max_frontier,
                     args.max_hypotheses)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    # An invalid certificate indicates a correctness defect, not mere scarcity.
    return 0 if record["status"] == "verified" else (3 if record["status"] == "audit_invalid" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
