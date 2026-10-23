"""Independent, bounded audit of public-information Minesweeper certificates.

Python reference only. This intentionally does not call the frontier solver or
its game replay helper: it checks a proposed trace with a second constraint
enumerator and a separate zero-flood implementation. A search-budget failure
is never interpreted as proof that a click is safe.
"""
from __future__ import annotations


class AuditLimit(Exception):
    """The independent finite audit could not complete within its budget."""


def _neighbors(i: int, width: int, height: int) -> tuple[int, ...]:
    x, y = i % width, i // width
    return tuple(yy * width + xx
                 for yy in range(max(0, y - 1), min(height, y + 2))
                 for xx in range(max(0, x - 1), min(width, x + 2))
                 if (xx, yy) != (x, y))


def _component_counts(cells, constraints, target, budget, max_mines):
    """Feasible mine totals, and totals with the proposed click mined."""
    local = [(near, clue) for near, clue in constraints if near & cells]
    order = sorted(cells, key=lambda i: (-sum(i in near for near, _ in local), i))
    # Python recursion depth is not a proof of exhaustion. Reject explicitly.
    if len(order) > 900:
        raise AuditLimit("constraint component exceeds bounded recursion")
    touching = [[j for j, (near, _) in enumerate(local) if i in near]
                for i in order]
    needed = [clue for _, clue in local]
    remaining = [len(near) for near, _ in local]
    totals, target_mined = set(), set()

    def search(position, count, selected):
        budget[0] += 1
        if budget[0] > budget[1]:
            raise AuditLimit("independent certificate audit budget exhausted")
        if position == len(order):
            if all(need == 0 for need in needed):
                totals.add(count)
                if selected:
                    target_mined.add(count)
            return
        cell = order[position]
        for value in (0, 1):
            next_count = count + value
            if next_count > max_mines:
                continue
            for j in touching[position]:
                needed[j] -= value
                remaining[j] -= 1
            if all(0 <= needed[j] <= remaining[j] for j in touching[position]):
                search(position + 1, next_count,
                       selected or (cell == target and value == 1))
            for j in touching[position]:
                needed[j] += value
                remaining[j] += 1

    search(0, 0, False)
    return totals, target_mined


def independently_forced_safe(width: int, height: int, mine_count: int,
                              opened: dict[int, int], click: int,
                              node_limit: int = 200_000) -> bool:
    """Decide whether every compatible board leaves ``click`` mine-free.

    Returns False for a possible mine. Contradictory public information raises
    ValueError; exhausted search raises AuditLimit. Neither permits a click.
    """
    if (type(width) is not int or type(height) is not int
            or width < 1 or height < 1 or width * height > 10_000
            or type(mine_count) is not int or not 0 <= mine_count < width * height
            or type(click) is not int or not 0 <= click < width * height
            or type(node_limit) is not int or node_limit < 1
            or not isinstance(opened, dict)):
        raise ValueError("invalid independent audit request")
    cells = width * height
    for i, clue in opened.items():
        if (type(i) is not int or not 0 <= i < cells
                or type(clue) is not int
                or not 0 <= clue <= len(_neighbors(i, width, height))):
            raise ValueError("invalid public clue")
    if click in opened:
        raise ValueError("click was already opened")
    hidden = set(range(cells)) - opened.keys()
    if mine_count > len(hidden):
        raise ValueError("not enough hidden cells for mine count")
    constraints = []
    frontier = set()
    for i, clue in opened.items():
        near = frozenset(set(_neighbors(i, width, height)) & hidden)
        if clue > len(near):
            raise ValueError("public clue is impossible")
        constraints.append((near, clue))
        frontier.update(near)

    parent = {i: i for i in frontier}

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for near, _ in constraints:
        if near:
            first = min(near)
            for i in near:
                parent[root(i)] = root(first)
    components = {}
    for i in frontier:
        components.setdefault(root(i), set()).add(i)

    budget = [0, node_limit]
    all_totals = {0}
    mined_totals = set()
    for component in components.values():
        counts, selected = _component_counts(component, constraints, click,
                                             budget, mine_count)
        if not counts:
            raise ValueError("no assignment satisfies public clues")
        mined_totals = ({a + b for a in mined_totals for b in counts
                         if a + b <= mine_count}
                        | {a + b for a in all_totals for b in selected
                           if a + b <= mine_count})
        all_totals = {a + b for a in all_totals for b in counts
                      if a + b <= mine_count}

    outside_count = len(hidden - frontier)
    feasible = {count for count in all_totals
                if 0 <= mine_count - count <= outside_count}
    if not feasible:
        raise ValueError("no board satisfies all public information")
    if click not in frontier:
        # Outside variables are interchangeable: if even one outside mine is
        # possible, this particular outside cell cannot be certified safe.
        return not any(1 <= mine_count - count <= outside_count
                       for count in feasible)
    return not any(0 <= mine_count - count <= outside_count
                   for count in mined_totals)


def audit_certificate(cert, node_limit: int = 200_000) -> bool:
    """Independently replay all zero-floods and certify each later click.

    Uses the hidden mines only to simulate game observations. Inference sees
    the opened clue dictionary, dimensions and total mine count, never truth.
    """
    try:
        width, height = cert.width, cert.height
        mine_count, first_click = cert.mine_count, cert.first_click
        mines, clicks = cert.mines, cert.clicks
        if (type(width) is not int or type(height) is not int
                or width < 1 or height < 1 or width * height > 10_000
                or type(mine_count) is not int
                or not 0 <= mine_count < width * height
                or type(first_click) is not int
                or not 0 <= first_click < width * height
                or type(node_limit) is not int or node_limit < 1
                or not isinstance(mines, frozenset)
                or len(mines) != mine_count
                or any(type(i) is not int or not 0 <= i < width * height
                       for i in mines)
                or not isinstance(clicks, tuple) or not clicks
                or clicks[0] != first_click
                or any(type(i) is not int or not 0 <= i < width * height
                       for i in clicks)):
            return False
        opened = {}
        for step, click in enumerate(clicks):
            if click in opened or click in mines:
                return False
            if step and not independently_forced_safe(
                    width, height, mine_count, opened, click, node_limit):
                return False
            pending = [click]
            while pending:
                cell = pending.pop()
                if cell in opened:
                    continue
                if cell in mines:
                    return False
                near = _neighbors(cell, width, height)
                clue = sum(i in mines for i in near)
                opened[cell] = clue
                if clue == 0:
                    pending.extend(i for i in near if i not in opened)
            if len(opened) == width * height - mine_count:
                return step == len(clicks) - 1
        return False
    except (AttributeError, TypeError, ValueError, AuditLimit, RecursionError):
        return False
