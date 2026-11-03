"""Independent, bounded audit of a no-guess N x N certificate.

No imports from the candidate generator, game oracle, or inference engine.
The checker reconstructs actual clues and zero expansion from the mine set,
then enumerates *all* mine placements consistent with each public view.
This finite oracle is intentionally exponential and intended for small boards.
"""
from dataclasses import dataclass
from itertools import combinations
from math import comb


@dataclass(frozen=True)
class Audit:
    status: str  # valid, invalid, or limit
    checked_clicks: int = 0
    opened_count: int = 0
    reason: str = ""


def _neighbors(n, i):
    x, y = i % n, i // n
    return tuple(yy*n + xx for yy in range(max(0, y-1), min(n, y+2))
                 for xx in range(max(0, x-1), min(n, x+2))
                 if (xx, yy) != (x, y))


def _reveal(n, mines, opened, index):
    """Apply a real click, including zero flood; caller checks mine safety."""
    todo = [index]
    while todo:
        cell = todo.pop()
        if cell in opened:
            continue
        around = _neighbors(n, cell)
        clue = sum(neighbor in mines for neighbor in around)
        opened[cell] = clue
        if clue == 0:
            todo.extend(j for j in around if j not in opened)


def _safe_choices(n, mine_count, opened, max_hypotheses):
    """Return (status, sorted safe cells) from only public observations."""
    hidden = tuple(i for i in range(n*n) if i not in opened)
    if mine_count > len(hidden):
        return "invalid", ()
    if comb(len(hidden), mine_count) > max_hypotheses:
        return "limit", ()
    possible = 0
    union = set()
    for placement in combinations(hidden, mine_count):
        candidate = set(placement)
        if all(sum(j in candidate for j in _neighbors(n, i)) == clue
               for i, clue in opened.items()):
            possible += 1
            union.update(candidate)
    if not possible:
        return "invalid", ()
    return "ok", tuple(i for i in hidden if i not in union)


def audit(n, mines, first, clicks, opened_count, max_hypotheses=100000):
    """Audit a generator witness for a fixed first click and min-safe policy.

    ``limit`` means the independent exhaustive oracle did not finish; it is
    never a successful certificate. The first click is an explicit safety
    assumption, not a deduction from an empty public board.
    """
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("board size")
    if type(first) is not int or not 0 <= first < n*n:
        raise ValueError("first click")
    if type(opened_count) is not int or not 0 <= opened_count <= n*n:
        raise ValueError("opened count")
    if type(max_hypotheses) is not int or max_hypotheses < 1:
        raise ValueError("hypothesis limit")
    try:
        mines = tuple(mines)
        clicks = tuple(clicks)
    except TypeError as exc:
        raise ValueError("mines/clicks") from exc
    if (any(type(i) is not int or not 0 <= i < n*n for i in mines)
            or tuple(sorted(set(mines))) != mines or len(mines) == n*n):
        raise ValueError("mine positions must be sorted, unique and non-full")
    if (not clicks or clicks[0] != first or
            any(type(i) is not int or not 0 <= i < n*n for i in clicks)):
        raise ValueError("click sequence")
    truth = set(mines)
    if first in truth:
        return Audit("invalid", reason="first click is mined")
    opened = {}
    for k, cell in enumerate(clicks):
        if cell in opened:
            return Audit("invalid", k, len(opened), "redundant click")
        if cell in truth:
            return Audit("invalid", k, len(opened), "mine clicked")
        if k:
            status, safe = _safe_choices(n, len(truth), opened,
                                         max_hypotheses)
            if status == "limit":
                return Audit("limit", k, len(opened), "hypothesis budget")
            if status != "ok" or not safe or cell != safe[0]:
                return Audit("invalid", k, len(opened),
                             "not the smallest publicly forced safe cell")
        _reveal(n, truth, opened, cell)
        if len(opened) == n*n - len(truth) and k != len(clicks)-1:
            return Audit("invalid", k+1, len(opened), "clicks after victory")
    if len(opened) != opened_count:
        return Audit("invalid", len(clicks), len(opened), "opened count mismatch")
    if len(opened) != n*n - len(truth):
        return Audit("invalid", len(clicks), len(opened), "not a victory")
    return Audit("valid", len(clicks), len(opened))
