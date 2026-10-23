"""Bounded exact public-information inference for N x N Minesweeper.

This is a Python reference, not a Bend implementation or a generator.
Only size, total mine count, opened (index, clue) pairs, and flags are inputs.
Flags are *not* assumed correct: they remain unknown mine candidates.
The search enumerates frontier assignments, not full-board configurations.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Inference:
    status: str  # "ok", "contradiction", or "limit"
    safe: tuple[int, ...] = ()  # Unopened, unflagged, certainly safe cells.
    forced_mines: tuple[int, ...] = ()  # Certainly mined, flags included.


def infer(n, mine_count, opened, flags=(), max_frontier=18):
    """Infer only forced cells; never guess when no safe cell is known.

    A result of ``limit`` means the frontier is too large to enumerate,
    not that the public observations are inconsistent. A result of ``ok``
    with an empty ``safe`` is a valid, possibly guess-requiring position.
    """
    if (type(n) is not int or not 2 <= n <= 100 or
            type(mine_count) is not int or not 0 <= mine_count <= n*n or
            type(max_frontier) is not int or not 0 <= max_frontier <= 24):
        raise ValueError("size, mine count, or frontier limit")
    try:
        observations = tuple(opened)
        marked = tuple(flags)
    except TypeError as exc:
        raise ValueError("opened/flags") from exc
    clues = {}
    for item in observations:
        if (not isinstance(item, (tuple, list)) or len(item) != 2 or
                type(item[0]) is not int or not 0 <= item[0] < n*n or
                type(item[1]) is not int or not 0 <= item[1] <= 8 or
                item[0] in clues):
            raise ValueError("opened cell or clue")
        clues[item[0]] = item[1]
    if (any(type(i) is not int or not 0 <= i < n*n or i in clues
            for i in marked) or len(set(marked)) != len(marked)):
        raise ValueError("flags")

    hidden = set(range(n*n)) - clues.keys()
    if mine_count > len(hidden):
        return Inference("contradiction")
    constraints = []
    frontier = set()
    for i, clue in clues.items():
        x, y = i % n, i // n
        around = {yy*n + xx
                  for yy in range(max(0, y-1), min(n, y+2))
                  for xx in range(max(0, x-1), min(n, x+2))
                  if (xx, yy) != (x, y) and yy*n+xx in hidden}
        if clue > len(around):
            return Inference("contradiction")
        constraints.append((around, clue))
        frontier.update(around)
    if len(frontier) > max_frontier:
        return Inference("limit")

    cells = sorted(frontier)
    bit_of = {cell: 1 << k for k, cell in enumerate(cells)}
    masks = [(sum(bit_of[i] for i in around), clue)
             for around, clue in constraints]
    free = hidden - frontier
    feasible = 0
    mine_union = 0
    mine_intersection = (1 << len(cells)) - 1
    remaining_counts = set()
    for mask in range(1 << len(cells)):
        remaining = mine_count - mask.bit_count()
        if not 0 <= remaining <= len(free):
            continue
        if any((mask & bits).bit_count() != clue for bits, clue in masks):
            continue
        feasible += 1
        mine_union |= mask
        mine_intersection &= mask
        remaining_counts.add(remaining)
    if feasible == 0:
        return Inference("contradiction")

    safe = {cell for k, cell in enumerate(cells)
            if not mine_union & (1 << k)}
    forced = {cell for k, cell in enumerate(cells)
              if mine_intersection & (1 << k)}
    if remaining_counts == {0}:
        safe.update(free)
    if remaining_counts == {len(free)}:
        forced.update(free)
    safe.difference_update(marked)  # Flags are hypotheses, not verified mines.
    return Inference("ok", tuple(sorted(safe)), tuple(sorted(forced)))
