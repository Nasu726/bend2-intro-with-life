"""Independent bounded verifier for public-safe N x N click certificates.

The *truth* mine set is used only to reconstruct game observations. Every
post-first-click safety decision is made from (size, total mines, opened
numbers) by enumerating the whole visible frontier, with the unobserved
remainder accounted for by its mine-count capacity. This module imports
neither the game oracle nor the component-DP inference implementation.

A 'valid' result is a finite certificate for the supplied placement and
click sequence, not a proof that every board can be solved without guessing.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Audit:
    status: str  # valid / invalid / limit
    checked_clicks: int = 0
    opened_count: int = 0
    reason: str = ""


def _neighbors(n, cell):
    x, y = cell % n, cell // n
    return tuple(yy*n + xx for yy in range(max(0, y-1), min(n, y+2))
                 for xx in range(max(0, x-1), min(n, x+2))
                 if (xx, yy) != (x, y))


def _reveal(n, mines, opened, first):
    pending = [first]
    while pending:
        cell = pending.pop()
        if cell in opened:
            continue
        if cell in mines:
            raise AssertionError("zero expansion reached a mine")
        neighbors = _neighbors(n, cell)
        clue = sum(other in mines for other in neighbors)
        opened[cell] = clue
        if clue == 0:
            pending.extend(other for other in neighbors if other not in opened)


def _publicly_safe(n, mine_count, opened, target, max_frontier):
    """Return 'safe', 'guess', 'contradiction' or 'limit'.

    This function must never receive the true mine set. A frontier mask is
    feasible if it satisfies every visible clue and the *remaining* mine
    count can be assigned to non-frontier hidden cells. Those cells are
    interchangeable, so a non-frontier target is safe only when every
    feasible mask leaves zero mines for the free region.
    """
    hidden = set(range(n*n)) - opened.keys()
    if target not in hidden:
        return "guess"
    frontier = sorted({neighbor for cell in opened
                       for neighbor in _neighbors(n, cell)
                       if neighbor in hidden})
    if len(frontier) > max_frontier:
        return "limit"
    free_count = len(hidden) - len(frontier)
    position = {cell: k for k, cell in enumerate(frontier)}
    constraints = []
    for cell, clue in opened.items():
        bits = sum(1 << position[j] for j in _neighbors(n, cell)
                   if j in position)
        constraints.append((bits, clue))

    target_bit = position.get(target)
    any_model = False
    possibly_mined = False
    for mask in range(1 << len(frontier)):
        remaining = mine_count - mask.bit_count()
        if not 0 <= remaining <= free_count:
            continue
        if any((mask & bits).bit_count() != clue for bits, clue in constraints):
            continue
        any_model = True
        if (bool(mask & (1 << target_bit)) if target_bit is not None
                else remaining > 0):
            possibly_mined = True
            break
    if not any_model:
        return "contradiction"
    return "guess" if possibly_mined else "safe"


def audit(n, mines, first, clicks, expected_opened, *, max_frontier=18):
    """Validate a no-guess trace for an unchanged, first-click-safe board.

    Unlike the ordinary game reference, this certificate does *not* relocate
    a first-click mine. A limit is inconclusive, never an accepted proof.
    The verifier accepts any publicly forced safe-cell selection order.
    """
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("board size")
    if type(first) is not int or not 0 <= first < n*n:
        raise ValueError("first click")
    if type(expected_opened) is not int or not 0 <= expected_opened <= n*n:
        raise ValueError("opened count")
    if type(max_frontier) is not int or not 0 <= max_frontier <= 20:
        raise ValueError("frontier limit")
    if not isinstance(mines, (tuple, list, frozenset, set)):
        raise ValueError("mine positions")
    if not isinstance(clicks, (tuple, list)):
        raise ValueError("click sequence")
    if (any(type(i) is not int or not 0 <= i < n*n for i in mines)
            or len(set(mines)) != len(mines) or len(mines) >= n*n):
        raise ValueError("mine positions")
    if (not clicks or clicks[0] != first or
            any(type(i) is not int or not 0 <= i < n*n for i in clicks)):
        raise ValueError("click sequence")
    truth = frozenset(mines)
    if first in truth:
        return Audit("invalid", reason="first click is mined")
    opened = {}
    for step, cell in enumerate(clicks):
        if cell in opened:
            return Audit("invalid", step, len(opened), "redundant click")
        if cell in truth:
            return Audit("invalid", step, len(opened), "mine clicked")
        if step:
            decision = _publicly_safe(n, len(truth), opened, cell,
                                      max_frontier)
            if decision == "limit":
                return Audit("limit", step, len(opened), "frontier budget")
            if decision != "safe":
                return Audit("invalid", step, len(opened),
                             "not publicly forced safe: " + decision)
        _reveal(n, truth, opened, cell)
        if len(opened) == n*n - len(truth) and step != len(clicks)-1:
            return Audit("invalid", step+1, len(opened), "clicks after victory")
    if len(opened) != expected_opened:
        return Audit("invalid", len(clicks), len(opened), "opened count mismatch")
    if len(opened) != n*n - len(truth):
        return Audit("invalid", len(clicks), len(opened), "not a victory")
    return Audit("valid", len(clicks), len(opened))


if __name__ == "__main__":
    print(audit(10, tuple(range(50, 60)), 0, (0, 99), 90))
    print(audit(10, tuple(range(50, 60)), 0, (0, 99), 90,
                max_frontier=9))
