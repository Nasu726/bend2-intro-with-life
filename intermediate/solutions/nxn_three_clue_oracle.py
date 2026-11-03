"""Independent whole-board oracle for a three-clue Minesweeper lesson.

This intentionally does not import the frontier/component solver. The
board is 3x3, with two mines and publicly revealed clues 0, 2, and 7.
It is a reference example, not a Bend N x N solver or generator.
A None mine_count removes the global-total constraint for an ablation check.
"""
from itertools import combinations

CLUES = ((0, 1), (2, 1), (7, 1))
MINE_COUNT = 2


def neighbors(n, cell):
    x, y = cell % n, cell // n
    return {other for other in range(n * n)
            if other != cell and abs(other % n - x) <= 1
            and abs(other // n - y) <= 1}


def enumerate_models(n, mine_count, clues):
    """Try every placement; do not inspect any hidden reference board."""
    opened = dict(clues)
    if len(opened) != len(clues):
        raise ValueError("duplicate public clue")
    hidden = sorted(set(range(n * n)) - opened.keys())
    # None means the global mine total is NOT public information.
    # Keep the same public clues and enumerate every feasible mine count.
    counts = range(len(hidden) + 1) if mine_count is None else (mine_count,)
    return tuple(tuple(placement)
                 for count in counts
                 for placement in combinations(hidden, count)
                 if all(len(set(placement) & neighbors(n, index)) == number
                        for index, number in clues))


def deductions(n, mine_count, clues):
    models = enumerate_models(n, mine_count, clues)
    if not models:
        return "contradiction", (), (), 0
    hidden = set(range(n * n)) - {index for index, _ in clues}
    possible = set().union(*(set(model) for model in models))
    forced = set.intersection(*(set(model) for model in models))
    return ("ok", tuple(sorted(hidden - possible)),
            tuple(sorted(forced)), len(models))


def main():
    for pair in combinations(CLUES, 2):
        print(f"two {tuple(i for i, _ in pair)}: {deductions(3, MINE_COUNT, pair)}")
    print(f"three: {deductions(3, MINE_COUNT, CLUES)}")
    print(f"models: {enumerate_models(3, MINE_COUNT, CLUES)}")
    print(f"without total: {deductions(3, None, CLUES)}")
    print(f"models without total: {enumerate_models(3, None, CLUES)}")


if __name__ == "__main__":
    main()
