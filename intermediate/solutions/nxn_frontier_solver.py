"""Exact public-information Minesweeper inference with bounded frontier search.

This is a Python *reference*, not the Bend game engine or a formal proof.
Unlike naive enumeration of all mine layouts, it enumerates only connected
components of the visible-number frontier.  Unconstrained hidden cells are
accounted for by the global mine count, without enumerating their subsets.

Only "Visible" enters inference. Hidden mine truth is accessible solely to
the separate certificate replay helper below. Exhaustion of the search budget
raises SearchLimit; it never returns a partial safety certificate.
"""
from __future__ import annotations

from collections import defaultdict

from noguess_reference import (SearchLimit, Visible, expose, neighbors)


def _constraints(view: Visible):
    if not isinstance(view, Visible):
        raise ValueError("expected a public Visible board")
    w, h, total = view.width, view.height, view.mine_count
    if (type(w) is not int or w <= 0 or type(h) is not int or h <= 0
            or type(total) is not int or not 0 <= total <= w * h
            or not isinstance(view.opened, tuple) or w * h > 10_000):
        raise ValueError("invalid public board dimensions or mine count")

    opened = {}
    for item in view.opened:
        if (not isinstance(item, tuple) or len(item) != 2
                or type(item[0]) is not int or type(item[1]) is not int):
            raise ValueError("invalid visible clue")
        i, clue = item
        if not (0 <= i < w * h and 0 <= clue <= len(neighbors(i, w, h))):
            raise ValueError("visible clue out of range")
        if i in opened and opened[i] != clue:
            raise ValueError("conflicting clues for one cell")
        opened[i] = clue
    hidden = set(range(w * h)) - opened.keys()
    if total > len(hidden):
        raise ValueError("more mines than hidden cells")

    raw = []
    for i, clue in opened.items():
        adjacent = frozenset(neighbors(i, w, h)) & hidden
        if not adjacent and clue:
            raise ValueError("visible clues are inconsistent")
        if clue > len(adjacent):
            raise ValueError("clue exceeds remaining neighbors")
        raw.append((adjacent, clue))
    frontier = set().union(*(cells for cells, _ in raw)) if raw else set()
    return total, hidden, frontier, raw


def _components(frontier, constraints):
    """Connected components of variables sharing a visible clue."""
    parent = {v: v for v in frontier}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for cells, _ in constraints:
        if not cells:
            continue
        first = min(cells)
        for v in cells:
            parent[find(v)] = find(first)
    groups = defaultdict(set)
    for v in frontier:
        groups[find(v)].add(v)
    return [tuple(sorted(group)) for group in groups.values()]


def _enumerate_component(cells, constraints, budget, max_mines):
    """Return count -> union of mined cells in every satisfying assignment."""
    cell_set = set(cells)
    local = [(near & cell_set, target)
             for near, target in constraints if near & cell_set]
    degree = {v: sum(v in near for near, _ in local) for v in cells}
    order = sorted(cells, key=lambda v: (-degree[v], v))
    if len(order) > 900:
        raise SearchLimit("frontier component too large for bounded recursion")
    touching = [[j for j, (near, _) in enumerate(local) if v in near]
                for v in order]
    need = [target for _, target in local]
    left = [len(near) for near, _ in local]
    union_by_count = {}

    def dfs(position, count, mask):
        budget[0] += 1
        if budget[0] > budget[1]:
            raise SearchLimit("frontier enumeration budget exhausted")
        if count > max_mines:
            return
        if position == len(order):
            if all(target == 0 for target in need):
                union_by_count[count] = union_by_count.get(count, 0) | mask
            return
        for value in (0, 1):
            touched = touching[position]
            for j in touched:
                left[j] -= 1
                need[j] -= value
            if all(0 <= need[j] <= left[j] for j in touched):
                dfs(position + 1, count + value,
                    mask | (1 << position) if value else mask)
            for j in touched:
                need[j] += value
                left[j] += 1

    dfs(0, 0, 0)
    return order, union_by_count


def provably_safe_frontier(view: Visible, node_limit: int = 200_000) -> frozenset[int]:
    """Return *all* hidden cells safe in every consistent full board.

    Exact relative to the supplied public clues and global mine count.  A
    SearchLimit or inconsistent observation is a rejection, not permission to
    guess.  The caller must not turn either exception into a safety claim.
    """
    if type(node_limit) is not int or node_limit < 1:
        raise ValueError("node_limit must be a positive integer")
    total, hidden, frontier, constraints = _constraints(view)
    outside = hidden - frontier
    budget = [0, node_limit]
    groups = []
    for component in _components(frontier, constraints):
        order, unions = _enumerate_component(component, constraints, budget, total)
        if not unions:
            raise ValueError("visible clues are inconsistent")
        groups.append((order, unions))

    prefix = [{0}]
    for _, unions in groups:
        prefix.append({a + b for a in prefix[-1] for b in unions if a + b <= total})
    suffix = [set() for _ in range(len(groups) + 1)]
    suffix[-1] = {0}
    for j in range(len(groups) - 1, -1, -1):
        suffix[j] = {a + b for a in suffix[j + 1]
                     for b in groups[j][1] if a + b <= total}

    possible = {s for s in prefix[-1] if 0 <= total - s <= len(outside)}
    if not possible:
        raise ValueError("no mine layout satisfies the public information")

    safe = set()
    for j, (order, unions) in enumerate(groups):
        allowed_masks = 0
        for count, mask in unions.items():
            if any(0 <= total - (before + count + after) <= len(outside)
                   for before in prefix[j] for after in suffix[j + 1]):
                allowed_masks |= mask
        safe.update(cell for bit, cell in enumerate(order)
                    if not (allowed_masks & (1 << bit)))

    if outside and all(total == frontier_mines for frontier_mines in possible):
        safe.update(outside)
    return frozenset(safe)


def verify_no_guess_frontier(width: int, height: int, mines: frozenset[int],
                             first_click: int, node_limit: int = 200_000):
    """Replay safe clicks using public-only deduction; reject any stalemate.

    The verifier (not the solver) knows the true mine set.  Returns a trace
    only if the entire board is opened without guessing.  None is not proof
    that no winning no-guess trace exists: a different safe-click order might.
    """
    if (type(width) is not int or width <= 0 or type(height) is not int
            or height <= 0 or not isinstance(mines, frozenset)
            or any(type(i) is not int or not 0 <= i < width * height for i in mines)
            or len(mines) >= width * height or width * height > 10_000
            or type(first_click) is not int or not 0 <= first_click < width * height
            or type(node_limit) is not int or node_limit < 1):
        raise ValueError("invalid no-guess verification request")
    if first_click in mines:
        return None
    view = expose(mines, Visible(width, height, len(mines), ()), first_click)
    trace = [first_click]
    while len(view.opened) < width * height - len(mines):
        try:
            safe = provably_safe_frontier(view, node_limit=node_limit)
        except (SearchLimit, ValueError):
            return None
        if not safe:
            return None
        move = min(safe)
        if move in mines:
            raise AssertionError("public solver incorrectly certified a mine")
        view = expose(mines, view, move)
        trace.append(move)
    return tuple(trace)
