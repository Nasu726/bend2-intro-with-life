#!/usr/bin/env python3
"""Independent geometry oracle plus Bend execution for public-only neighbors.

The rule must never inspect a true mine mask or assume flags are correct.
The generated Bend tests compare exact ordered lists, not just counts.
"""
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ("nxn_geometry.bend", "nxn_neighbors.bend",
         "nxn_public_subset.bend", "nxn_public_neighbors.bend")


def oracle(n, clue, opened):
    if clue not in opened or not 0 <= clue < n * n:
        return ()
    x, y = clue % n, clue // n
    return tuple(i for i in range(n * n) if i not in opened
                 and i != clue and abs(i % n - x) <= 1
                 and abs(i // n - y) <= 1)


def cases():
    # Named examples from the textbook's three-clue and four-clue lessons.
    result = [(3, 0, (0, 2, 7)), (3, 2, (0, 2, 7)),
              (3, 7, (0, 2, 7)),
              (4, 0, (0, 1, 2, 4)), (4, 1, (0, 1, 2, 4)),
              (4, 2, (0, 1, 2, 4)), (4, 4, (0, 1, 2, 4)),
              (2, 0, (0, 1, 2, 3)),
              (2, 0, (0,)), (4, 3, (0, 1, 2, 4)),
              (4, 16, (0, 1, 2, 4)),
              (10, 0, (0, 1, 10)), (10, 99, (99,)),
              (17, 144, (126, 127, 143, 144, 145, 160, 161)),
              (100, 0, (0, 1, 100)),
              (100, 9999, (9898, 9899, 9998, 9999))]
    rng = random.Random(20261026)
    for n in (2, 3, 4, 10, 17, 100):
        for _ in range(3):
            clue = rng.randrange(n * n)
            opened = set(rng.sample(range(n * n), min(n * n, 7)))
            opened.add(clue)
            result.append((n, clue, tuple(sorted(opened))))
    assert oracle(3, 0, (0, 2, 7)) == (1, 3, 4)
    assert oracle(3, 2, (0, 2, 7)) == (1, 4, 5)
    assert oracle(3, 7, (0, 2, 7)) == (3, 4, 5, 6, 8)
    assert oracle(4, 0, (0, 1, 2, 4)) == (5,)
    assert oracle(4, 1, (0, 1, 2, 4)) == (5, 6)
    return result


def list_literal(items):
    return "[" + ", ".join(map(str, items)) + "]"


def program(batch):
    lines = [
        "import Base", "import ./nxn_public_neighbors.bend as Rule", "",
        "def equal(actual: List<U32>, expected: List<U32>) -> Bool:",
        "  match actual:",
        "    case Nil{}:",
        "      match expected:",
        "        case Nil{}:", "          True{}",
        "        case y <> ys:", "          False{}",
        "    case x <> xs:",
        "      match expected:",
        "        case Nil{}:", "          False{}",
        "        case y <> ys:",
        "          Bool.and(U32.is_eq(x, y), equal(xs, ys))", "",
        "def yes(value: Bool) -> U32:",
        "  match value:", "    case True{}:", "      1",
        "    case False{}:", "      0", "",
    ]
    for i, (n, clue, opened) in enumerate(batch):
        expected = oracle(n, clue, opened)
        lines.extend((f"def case_{i}() -> U32:",
                      "  yes(equal(Rule.unknown_neighbors("
                      f"{n}, {clue}, {list_literal(opened)}), "
                      f"{list_literal(expected)}))", ""))
    lines.extend(("def main() -> U32:",
                  "  (" + " + ".join(f"case_{i}()" for i in range(len(batch)))
                  + " : U32)", ""))
    return "\n".join(lines)


def run_bend(path, expected):
    for check_only in (True, False):
        args = ["bend", str(path)] + (["--check-only"] if check_only else [])
        p = subprocess.run(args, cwd=path.parent, capture_output=True,
                           text=True, timeout=120,
                           env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if p.returncode:
            raise AssertionError(f"{args}: {p.stdout}\n{p.stderr}")
        if not check_only and p.stdout.strip().splitlines()[-1] != str(expected):
            raise AssertionError(f"{path.name}: expected {expected}, got {p.stdout}")


def main():
    checks = cases()
    if "--oracle-only" in sys.argv:
        for n, clue, opened in checks:
            assert all(0 <= i < n*n and i not in opened for i in oracle(n, clue, opened))
        print(f"PASS {len(checks)} public-only geometry oracle cases")
        return
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for filename in FILES:
            shutil.copyfile(ROOT / "minesweeper" / filename, folder / filename)
        run_bend(folder / "nxn_public_neighbors.bend", 5)
        for start in range(0, len(checks), 4):
            batch = checks[start:start + 4]
            source = folder / f"check_public_neighbors_{start}.bend"
            source.write_text(program(batch), encoding="utf-8")
            print(f"CHECK exact public-neighbor lists {start+1}-"
                  f"{start+len(batch)}/{len(checks)}", flush=True)
            run_bend(source, len(batch))
    print(f"PASS {len(checks)} Bend/Python exact public-neighbor lists")


if __name__ == "__main__":
    main()
