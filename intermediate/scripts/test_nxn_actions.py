#!/usr/bin/env python3
"""Finite Bend-vs-independent-Python checks for one-cell N x N actions.

This deliberately does NOT test first-click relocation, zero cascade,
win detection, GUI, or no-guess generation. The expected observations
come from a coordinate-set model, not from the Bend word storage.
"""
from pathlib import Path
import os
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("nxn_geometry.bend", "nxn_mine_words.bend", "nxn_clues.bend",
           "nxn_actions.bend")


def reference(n, mines, actions, read):
    opened, flags, lost = set(), set(), False
    for op, i in actions:
        if lost or not 0 <= i < n*n:
            continue
        if op == "mark":
            if i not in opened:
                if i in flags:
                    flags.remove(i)
                else:
                    flags.add(i)
        elif op == "click":
            if i in flags or i in opened:
                continue
            if i in mines:
                lost = True
            else:
                opened.add(i)  # No zero cascade in this milestone.
        else:
            raise ValueError(op)
    if not 0 <= read < n*n:
        public = 12
    elif read in opened:
        x, y = read % n, read // n
        public = sum(max(abs(j % n - x), abs(j // n - y)) == 1
                     for j in mines)
    elif read in flags:
        public = 11
    else:
        public = 10
    return public, int(lost)


def build_cases():
    rng = random.Random(20261024)
    result = []
    for n in (2, 3, 4, 10, 17, 100):
        last = n*n-1
        mines = {1, last}
        patterns = [
            ((), 0),
            (("click", 0), 0),
            (("click", 1), 1),
            (("mark", 1), 1),
            (("mark", 1), ("click", 1)),
            (("mark", 1), ("mark", 1), ("click", 1)),
            (("click", 0), ("mark", 0)),
            (("click", 1), ("click", 0)),
            (("click", n*n), ("mark", 2**32-1)),
            (("click", 0), ("click", 0)),
            (("mark", last), ("click", last)),
            (("click", last), ("mark", 0)),
        ]
        for p in patterns:
            if len(p) == 2 and isinstance(p[1], int):
                actions, read = p[0], p[1]
                if isinstance(actions, tuple) and actions and isinstance(actions[0], str):
                    actions = (actions,)
            else:
                actions, read = p, (p[-1][1] if p else 0)
            result.append((n, tuple(sorted(mines)), tuple(actions), read))
        for _ in range(6):
            actions = tuple((rng.choice(("click", "mark")),
                             rng.choice((0, 1, last, n*n, 2**32-1,
                                         rng.randrange(n*n))))
                            for _ in range(3))
            read = rng.choice((0, 1, last, n*n, 2**32-1))
            result.append((n, tuple(sorted(mines)), actions, read))
    return result


def bend_source(cases):
    lines = ["import Base", "import ./nxn_mine_words.bend as Words",
             "import ./nxn_actions.bend as Actions", "",
             "def bit(b: Bool) -> U32:", "  match b:",
             "    case True{}:", "      1", "    case False{}:", "      0", "",
             "def checked_pair(expected_public: U32, expected_lost: U32, pair: Actions.State & U32) -> U32:",
             "  (state, value) = pair",
             "  (bit(U32.is_eq(value, expected_public)) + bit(U32.is_eq(Actions.lost_code(state), expected_lost)) : U32)", ""]
    for case_id, (n, mines, actions, read) in enumerate(cases):
        public, lost = reference(n, set(mines), actions, read)
        lines += [f"def case_{case_id}() -> U32:", f"  mines = Words.new({n})"]
        for i in mines:
            lines.append(f"  mines = Words.set_checked(mines, {i}, True{{}})")
        lines.append("  state = Actions.new(mines)")
        for op, i in actions:
            lines.append(f"  state = Actions.{op}(state, {i})")
        lines.append(f"  checked_pair({public}, {lost}, Actions.public_at(state, {read}))")
        lines.append("")
    for offset in range(0, len(cases), 8):
        lines += [f"def group_{offset}() -> U32:",
                  "  (" + " + ".join(f"case_{i}()" for i in range(offset, min(offset+8, len(cases)))) + " : U32)", ""]
    lines += ["def main() -> U32:",
              "  (" + " + ".join(f"group_{i}()" for i in range(0, len(cases), 8)) + " : U32)"]
    return "\n".join(lines) + "\n"


def main():
    cases = build_cases()
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in MODULES:
            (folder / name).write_bytes((ROOT / "minesweeper" / name).read_bytes())
        entry = folder / "test_nxn_actions.bend"
        entry.write_text(bend_source(cases), encoding="utf-8")
        for args in (("bend", str(entry), "--check-only"),
                     ("bend", str(entry))):
            print(f"CHECK N x N actions: {'typecheck' if len(args) == 3 else 'execution'} ({len(cases)} cases)", flush=True)
            p = subprocess.run(args, cwd=folder, capture_output=True, text=True,
                               timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
            if p.returncode:
                raise AssertionError(f"{args}: {p.stdout}\n{p.stderr}")
            if len(args) == 2 and p.stdout.strip().splitlines()[-1] != str(2*len(cases)):
                raise AssertionError(f"N x N actions mismatch: {p.stdout} != {2*len(cases)}")
    print(f"PASS Bend N x N one-cell actions: {2*len(cases)} finite observations")


if __name__ == "__main__":
    main()
