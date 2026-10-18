"""Small, independent reference for no-guess Minesweeper verification.

For teaching and tests, NOT a production-sized solver.  Enumeration is
exponential and deliberately capped.  This belongs on GitHub only, not in
the reader ZIP.  The deduction function sees ONLY the visible information.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import random


class SearchLimit(Exception):
    """The bounded exhaustive checker cannot certify this position."""


class GenerationFailed(Exception):
    """No verified no-guess board within the fixed attempt budget."""


@dataclass(frozen=True)
class Visible:
    width: int
    height: int
    mine_count: int
    # (linear cell index, visible adjacent-mine count); no hidden solution here.
    opened: tuple[tuple[int, int], ...]


def _valid_public_shape(view: Visible) -> bool:
    """Reject bools/coercible values before treating public data as indices."""
    return (
        type(view.width) is int and view.width > 0
        and type(view.height) is int and view.height > 0
        and type(view.mine_count) is int and view.mine_count >= 0
        and isinstance(view.opened, tuple)
        and all(isinstance(item, tuple) and len(item) == 2
                and type(item[0]) is int and type(item[1]) is int
                for item in view.opened)
    )


def neighbors(index: int, width: int, height: int) -> tuple[int, ...]:
    x, y = index % width, index // width
    return tuple(
        yy * width + xx
        for yy in range(max(0, y - 1), min(height, y + 2))
        for xx in range(max(0, x - 1), min(width, x + 2))
        if (xx, yy) != (x, y)
    )


def consistent_models(view: Visible, limit: int = 200_000):
    """Enumerate every mine layout consistent with public numbers and total."""
    if not _valid_public_shape(view) or type(limit) is not int or limit < 0:
        return []
    cells = set(range(view.width * view.height))
    opened = {}
    for index, clue in view.opened:
        # Invalid public observations must never certify a safe move.
        if (index not in cells or
                not 0 <= clue <= len(neighbors(index, view.width, view.height)) or
                (index in opened and opened[index] != clue)):
            return []
        opened[index] = clue
    hidden = sorted(cells - opened.keys())
    if not (0 <= view.mine_count <= len(hidden)):
        return []
    total = 0
    models = []
    for placement in combinations(hidden, view.mine_count):
        total += 1
        if total > limit:
            raise SearchLimit("too many candidate layouts for this exact checker")
        mines = frozenset(placement)
        if all(sum(q in mines for q in neighbors(p, view.width, view.height)) == clue
               for p, clue in opened.items()):
            models.append(mines)
    return models


def provably_safe(view: Visible, limit: int = 200_000) -> frozenset[int]:
    """Only visible constraints enter here; the actual board is not an input."""
    models = consistent_models(view, limit=limit)
    if not models:
        raise ValueError("no mine layout satisfies the visible information")
    all_cells = set(range(view.width * view.height))
    hidden = all_cells - dict(view.opened).keys()
    potentially_mined = set().union(*models)
    return frozenset(hidden - potentially_mined)


def expose(mines: frozenset[int], view: Visible, index: int) -> Visible:
    """Game-engine operation (not part of deduction): zero-cell flood opening."""
    if not _valid_public_shape(view):
        raise ValueError("invalid public board shape")
    if type(index) is not int or not 0 <= index < view.width * view.height:
        raise ValueError("cell out of bounds")
    if not isinstance(mines, frozenset) or any(
            type(m) is not int or m < 0 or m >= view.width * view.height
            for m in mines):
        raise ValueError("mine out of bounds")
    if len(mines) != view.mine_count:
        raise ValueError("mine count does not match public view")
    # The game engine knows the ground truth. Reject a forged/stale public view
    # before any click, including clicking an already-open cell.
    observed = set()
    for cell, clue in view.opened:
        if cell < 0 or cell >= view.width * view.height:
            raise ValueError("opened cell out of bounds")
        if cell in observed:
            raise ValueError("duplicate opened cell")
        observed.add(cell)
        if cell in mines:
            raise ValueError("a mine cannot be in the opened view")
        actual = sum(n in mines for n in neighbors(cell, view.width, view.height))
        if clue != actual:
            raise ValueError("opened clue does not match the board")
    if index in mines:
        raise ValueError("attempt to open a mine")
    opened = dict(view.opened)
    pending = [index]
    while pending:
        p = pending.pop()
        if p in opened:
            continue
        if p in mines:
            raise AssertionError("mine reached from a zero")
        nearby = sum(q in mines for q in neighbors(p, view.width, view.height))
        opened[p] = nearby
        if nearby == 0:
            pending.extend(q for q in neighbors(p, view.width, view.height)
                           if q not in opened)
    return Visible(view.width, view.height, view.mine_count,
                   tuple(sorted(opened.items())))


def verify_no_guess(width: int, height: int, mines: frozenset[int],
                    first_click: int, limit: int = 200_000):
    """Returns a safe-open trace if accepted; None on stalemate or limit.

    Only this verifier can access the truth.  The inference step above cannot.
    """
    if width <= 0 or height <= 0:
        raise ValueError("invalid board dimensions")
    if any(m < 0 or m >= width * height for m in mines):
        raise ValueError("mine out of bounds")
    if not (0 <= first_click < width * height):
        raise ValueError("first click out of bounds")
    if first_click in mines:
        return None
    view = expose(mines, Visible(width, height, len(mines), ()), first_click)
    trace = [first_click]
    while len(view.opened) < width * height - len(mines):
        try:
            safe = provably_safe(view, limit=limit)
        except (SearchLimit, ValueError):
            return None
        if not safe:
            return None
        move = min(safe)
        assert move not in mines
        view = expose(mines, view, move)
        trace.append(move)
    return tuple(trace)


def generate(width: int, height: int, mine_count: int, first_click: int,
             seed: int, attempts: int = 100):
    """Generate-and-verify, never silently return an unverified fallback."""
    if width <= 0 or height <= 0 or attempts <= 0:
        raise ValueError("invalid board or attempt count")
    if not 0 <= first_click < width * height:
        raise ValueError("first click out of bounds")
    forbidden = {first_click, *neighbors(first_click, width, height)}
    allowed = sorted(set(range(width * height)) - forbidden)
    if not (0 <= mine_count <= len(allowed)):
        raise ValueError("too many mines for the protected first click")
    rng = random.Random(seed)
    for _ in range(attempts):
        mines = frozenset(rng.sample(allowed, mine_count))
        trace = verify_no_guess(width, height, mines, first_click)
        if trace is not None:
            return mines, trace
    raise GenerationFailed(f"no verified board in {attempts} attempts")


if __name__ == "__main__":
    layout, safe_trace = generate(4, 4, 2, 0, seed=2026)
    print("mines:", sorted(layout))
    print("safe clicks:", safe_trace)
