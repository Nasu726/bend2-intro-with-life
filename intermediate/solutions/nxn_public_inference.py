"""Bounded exact public-information inference for N x N Minesweeper.

This is a Python reference, not a Bend implementation or a generator.
Only size, total mine count, opened (index, clue) pairs, and flags are inputs.
Flags are *not* assumed correct: they remain unknown mine candidates.
Disconnected frontier components are enumerated separately; a global mine
budget then filters the local assignments before forced cells are reported.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Inference:
    status: str  # "ok", "contradiction", or "limit"
    safe: tuple[int, ...] = ()  # Unopened, unflagged, certainly safe cells.
    forced_mines: tuple[int, ...] = ()  # Certainly mined, flags included.


def _possible(prefix, suffix, target):
    """Can one prefix count and one suffix count sum to target?"""
    if target < 0:
        return False
    while prefix:
        lowest = prefix & -prefix
        count = lowest.bit_length() - 1
        if count > target:
            return False
        if (suffix >> (target - count)) & 1:
            return True
        prefix ^= lowest
    return False


def infer(n, mine_count, opened, flags=(), max_frontier=18):
    """Infer only forced cells; never guess when no safe cell is known.

    ``max_frontier`` bounds each *connected* frontier component, rather than
    the sum of all disconnected components. A ``limit`` result means at least
    one component is too large, not that the clues contradict each other.
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
        if around:
            constraints.append((around, clue))
            frontier.update(around)
        elif clue != 0:
            return Inference("contradiction")
    # Two frontier cells belong to one component if a public clue relates them.
    parent = {cell: cell for cell in frontier}

    def find(cell):
        while parent[cell] != cell:
            parent[cell] = parent[parent[cell]]
            cell = parent[cell]
        return cell

    for around, _ in constraints:
        first = min(around)
        for cell in around:
            parent[find(cell)] = find(first)
    components = {}
    for cell in sorted(frontier):
        components.setdefault(find(cell), []).append(cell)
    if any(len(cells) > max_frontier for cells in components.values()):
        return Inference("limit")

    component_constraints = {root: [] for root in components}
    for around, clue in constraints:
        component_constraints[find(min(around))].append((around, clue))
    # Per-component: mine count -> (union of mined cells, intersection).
    summaries = []
    cell_groups = []
    for root, cells in sorted(components.items(), key=lambda item: min(item[1])):
        bit_of = {cell: 1 << k for k, cell in enumerate(cells)}
        masks = [(sum(bit_of[cell] for cell in around), clue)
                 for around, clue in component_constraints[root]]
        buckets = {}
        for mask in range(1 << len(cells)):
            if any((mask & bits).bit_count() != clue for bits, clue in masks):
                continue
            count = mask.bit_count()
            if count in buckets:
                union, intersection = buckets[count]
                buckets[count] = (union | mask, intersection & mask)
            else:
                buckets[count] = (mask, mask)
        if not buckets:
            return Inference("contradiction")
        summaries.append(buckets)
        cell_groups.append(cells)

    free = hidden - frontier
    free_count = len(free)
    # A bit at position k means that exactly k mines can be allocated there.
    prefix = [1]
    for buckets in summaries:
        previous = prefix[-1]
        reachable = 0
        for count in buckets:
            reachable |= previous << count
        prefix.append(reachable)
    suffix = [0] * (len(summaries) + 1)
    suffix[-1] = (1 << (free_count + 1)) - 1  # Free cells can hold 0..F mines.
    for i in range(len(summaries) - 1, -1, -1):
        reachable = 0
        for count in summaries[i]:
            reachable |= suffix[i+1] << count
        suffix[i] = reachable
    if not (suffix[0] >> mine_count) & 1:
        return Inference("contradiction")

    safe = set()
    forced = set()
    for i, (cells, buckets) in enumerate(zip(cell_groups, summaries)):
        mine_union = 0
        mine_intersection = (1 << len(cells)) - 1
        for count, (union, intersection) in buckets.items():
            if _possible(prefix[i], suffix[i+1], mine_count - count):
                mine_union |= union
                mine_intersection &= intersection
        for k, cell in enumerate(cells):
            if not (mine_union >> k) & 1:
                safe.add(cell)
            if (mine_intersection >> k) & 1:
                forced.add(cell)

    # The unconstrained cells are interchangeable. Only a forced 0 or F
    # remaining mines makes an individual free cell certainly safe or mined.
    remaining_counts = set()
    counts = prefix[-1]
    while counts:
        lowest = counts & -counts
        remaining = mine_count - (lowest.bit_length() - 1)
        if 0 <= remaining <= free_count:
            remaining_counts.add(remaining)
        counts ^= lowest
    if remaining_counts == {0}:
        safe.update(free)
    if remaining_counts == {free_count}:
        forced.update(free)
    safe.difference_update(marked)  # Flags are hypotheses, not verified mines.
    return Inference("ok", tuple(sorted(safe)), tuple(sorted(forced)))
