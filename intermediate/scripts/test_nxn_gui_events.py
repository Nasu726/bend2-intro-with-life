#!/usr/bin/env python3
"""Finite OS-style Event routing check, not a real desktop GUI test."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from test_nxn_lazy_game import FILES, GAME
from test_nxn_gui_adapter import ADAPTER, oracle

EVENTS = GAME / "nxn_gui_events.bend"
SEED = 20261029
# Event constructors, independent reference result for cell 0.
CLICK = "Mouse{0, 0, 0, True{}}"
CASES = (
    ("empty", [], 300),
    ("close", ["Close{}"], 500),
    ("escape", ["Key{27, True{}}"], 500),
    ("escape-release", ["Key{27, False{}}"], 300),
    ("reset-r", ["Key{114, True{}}"], 300),
    ("reset-R", ["Key{82, True{}}"], 300),
    ("reset-release", ["Key{114, False{}}"], 300),
    ("outside", ["Mouse{320, 0, 0, True{}}"], 300),
    ("left-release", ["Mouse{0, 0, 0, False{}}"], 300),
    ("fresh-flag", ["Mouse{0, 0, 1, True{}}"], 300),
    ("middle", ["Mouse{0, 0, 2, True{}}"], 300),
    ("other-key", ["Key{65, True{}}"], 300),
    ("first-click", [CLICK], oracle(10, 10, SEED, ((0, 0, 0),), 0)),
    ("click-reset", [CLICK, "Key{114, True{}}"], 300),
    ("click-close", [CLICK, "Close{}"], 500),
    ("click-flag", [CLICK, "Mouse{32, 0, 1, True{}}"],
     oracle(10, 10, SEED, ((0, 0, 0), (32, 0, 1)), 0)),
)


def harness(cases):
    lines = [
        "import Base",
        "import ./nxn_gui_events.bend as EV",
        "import ./nxn_gui_adapter.bend as GUI",
        "import ./nxn_lazy_game.bend as Lazy", "",
        "def one_if_true(b: Bool) -> U32:",
        "  match b:",
        "    case True{}:", "      1",
        "    case False{}:", "      0", "",
        "def equal(a: U32, b: U32) -> U32:",
        "  one_if_true(U32.is_eq(a, b))", "",
        "def snapshot_or_closed(state: Maybe<Lazy.Game>, index: U32) -> U32:",
        "  match state:",
        "    case None{}:", "      500",
        "    case Some{game}:", "      GUI.snapshot(game, index)", "",
    ]
    calls = []
    for i, (label, events, answer) in enumerate(cases):
        event_list = "[" + ", ".join(events) + "]"
        lines.extend([
            f"def check_{i}() -> U32:",
            f"  equal(snapshot_or_closed(EV.handle_events({event_list}, GUI.reset_gui({SEED}), {SEED}), 0), {answer})",
            "",
        ])
        calls.append(f"check_{i}()")
    lines += ["def main() -> U32:", "  (" + " + ".join(calls) + " : U32)"]
    return "\n".join(lines) + "\n"


def preflight():
    source = EVENTS.read_text(encoding="utf-8")
    assert len(CASES) == 16
    assert len({label for label, _, _ in CASES}) == 16
    assert source.index("def event(") < source.index("def handle_events(")
    assert "GUI.pointer(game, x, y, button)" in source
    assert "Some{GUI.reset_gui(seed)}" in source
    assert "App.run(" not in source
    assert CASES[12][2] != 300
    assert CASES[13][2] == 300 and CASES[14][2] == 500
    print("PASS 16 independent GUI event reference expectations", flush=True)


def run_bend(path, cwd, expected, label):
    for cmd in (("bend", str(path), "--check-only"), ("bend", str(path))):
        print(f"CHECK {label}: {'typecheck' if len(cmd) == 3 else 'run'}", flush=True)
        proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True,
                              timeout=180, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if proc.returncode:
            raise AssertionError(f"{label}: {cmd}\n{proc.stdout}\n{proc.stderr}")
        if len(cmd) == 2 and proc.stdout.strip().splitlines()[-1] != str(expected):
            raise AssertionError(f"{label}: expected {expected}, got {proc.stdout!r}")


def main():
    preflight()
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_gui_events.py [--static-only]")
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        for path in (ADAPTER, EVENTS):
            (directory / path.name).write_bytes(path.read_bytes())
        for start in range(0, len(CASES), 4):
            group = CASES[start:start + 4]
            path = directory / f"gui_events_{start}.bend"
            path.write_text(harness(group), encoding="utf-8")
            run_bend(path, directory, len(group),
                     f"events {start + 1}-{start + len(group)}/{len(CASES)}")
    print("PASS 16 Bend event traces", flush=True)


if __name__ == "__main__":
    main()
