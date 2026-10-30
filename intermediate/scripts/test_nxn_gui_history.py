#!/usr/bin/env python3
"""Finite GUI action-history replay checks; no file I/O or OS window yet."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from test_nxn_lazy_game import FILES, GAME
from test_nxn_gui_adapter import ADAPTER, oracle

HISTORY = GAME / "nxn_gui_history.bend"
SEED = 20261029


def cases():
    original = f"H.pointer(H.new({SEED}), 0, 0, 0)"
    flagged = f"H.pointer({original}, 319, 319, 1)"
    return [
        ("fresh", f"H.snapshot(H.new({SEED}), 0)", 300),
        ("invalid-pixel", f"H.snapshot(H.pointer(H.new({SEED}), 321, 321, 0), 0)", 300),
        ("invalid-button", f"H.snapshot(H.pointer(H.new({SEED}), 0, 0, 2), 0)", 300),
        ("fresh-right", f"H.snapshot(H.pointer(H.new({SEED}), 319, 319, 1), 0)", 300),
        ("first-revealed", f"H.snapshot({original}, 0)", oracle(10, 10, SEED, ((0,0,0),), 0)),
        ("live-flag", f"H.snapshot({flagged}, 99)", 1),
        ("restore-flag", f"H.recovered_snapshot(H.restore({SEED}, [0, 199]), 99)", 1),
        ("restore-unflag", f"H.recovered_snapshot(H.restore({SEED}, [0, 199, 199]), 99)", 0),
        ("restore-first", f"H.recovered_snapshot(H.restore({SEED}, [0]), 0)",
         oracle(10,10,SEED,((0,0,0),),0)),
        ("restore-fresh", f"H.recovered_snapshot(H.restore({SEED}, Nil{{}}), 0)", 300),
        ("reject-outside", f"H.recovered_snapshot(H.restore({SEED}, [20000]), 0)", 600),
        ("reject-outside-middle", f"H.recovered_snapshot(H.restore({SEED}, [0, 20001]), 0)", 600),
        ("reset-clears", f"H.snapshot(H.reset({flagged}), 0)", 300),
        ("history-order", f"sum_codes(H.history({flagged}))", 199),
    ]


def generated(batch):
    lines = [
        "import Base",
        "import ./nxn_gui_history.bend as H",
        "",
        "def bit(equal: Bool) -> U32:",
        "  match equal:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0",
        "",
        "def equals(a: U32, b: U32) -> U32:",
        "  bit(U32.is_eq(a, b))",
        "",
        "def sum_codes(xs: List<&2, U32>) -> U32:",
        "  match xs:",
        "    case Nil{}:",
        "      0",
        "    case x <> rest:",
        "      (x + sum_codes(rest) : U32)",
        "",
    ]
    for i, (_, expression, expected) in enumerate(batch):
        lines += [f"def check_{i}() -> U32:",
                  f"  equals({expression}, {expected})", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"check_{i}()" for i in range(len(batch))) + " : U32)", ""]
    return "\n".join(lines)


def static_checks():
    source = HISTORY.read_text(encoding="utf-8")
    assert "type Model is Type:" in source
    assert "newest_first: List<&2, U32>" in source
    assert "def restore(" in source and "def history(" in source
    assert "U32.is_lt(entry, 20000)" in source
    assert "512n" in source
    assert "Lazy.generate(" not in source
    assert "Words.has(" not in source and "mines:" not in source
    assert len(cases()) == 14
    assert len({label for label, *_ in cases()}) == 14
    assert cases()[4][2] != 300
    assert cases()[6][2] == 1 and cases()[7][2] == 0
    print("PASS 14 independent GUI history expectations and static guard", flush=True)


def run(path, expected):
    for cmd in (("bend", str(path), "--check-only"), ("bend", str(path))):
        p = subprocess.run(cmd, cwd=path.parent, capture_output=True, text=True,
                           env=dict(os.environ, BEND_NO_TELEMETRY="1"), timeout=240)
        if p.returncode:
            raise AssertionError(f"{cmd}: {p.stdout}\n{p.stderr}")
        if len(cmd) == 2 and p.stdout.strip().splitlines()[-1] != str(expected):
            raise AssertionError(f"wanted {expected} successes, got {p.stdout!r}")


def main():
    static_checks()
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_gui_history.py [--static-only]")
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        for path in (ADAPTER, HISTORY):
            (directory / path.name).write_bytes(path.read_bytes())
        checks = cases()
        for start in range(0, len(checks), 3):
            group = checks[start:start + 3]
            sample = directory / f"gui_history_{start}.bend"
            sample.write_text(generated(group), encoding="utf-8")
            run(sample, len(group))
    print("PASS 14 GUI history Bend replay checks (no disk I/O or OS window)", flush=True)


if __name__ == "__main__":
    main()
