"""Public-clue adapter for the Bend six-bit, three-constraint kernel.

This produces *inputs*, not a proof or a general N x N solver.  It never
accepts the true mine layout or treats a player's flag as known evidence.
The Bend kernel always enumerates six bits, so a frontier of any other size
must not be silently padded or truncated.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ThreeClueInput:
    cells: tuple[int, ...]             # bit position -> board cell
    masks: tuple[int, int, int]
    counts: tuple[int, int, int]
    total: int                         # meaningful only when use_total
    use_total: bool

    def bend_arguments(self):
        a, b, c = self.masks
        ra, rb, rc = self.counts
        return (a, b, c, ra, rb, rc, self.total, self.use_total)


def _neighbors(n, index):
    x, y = index % n, index // n
    return {yy * n + xx
            for yy in range(max(0, y - 1), min(n, y + 2))
            for xx in range(max(0, x - 1), min(n, x + 2))
            if yy * n + xx != index}


def from_public_clues(n, opened, mine_count=None):
    """Build an exact six-cell kernel input or return None (unsupported size).

    Only three (cell, clue) observations are accepted.  A global mine total
    is used only when *every* hidden cell is represented by the six bits.
    Otherwise imposing it on the frontier would falsely assert that there
    are no mines outside the frontier.  In that case the kernel still gives
    sound local deductions, but may miss deductions requiring the total.
    """
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("board size")
    try:
        clues = tuple(opened)
    except TypeError as exc:
        raise ValueError("opened clues") from exc
    if len(clues) != 3:
        raise ValueError("exactly three public clues required")
    seen = set()
    for item in clues:
        if (not isinstance(item, (tuple, list)) or len(item) != 2 or
                type(item[0]) is not int or not 0 <= item[0] < n * n or
                type(item[1]) is not int or not 0 <= item[1] <= 8 or
                item[0] in seen):
            raise ValueError("invalid or duplicate public clue")
        seen.add(item[0])
    if (mine_count is not None and
            (type(mine_count) is not int or
             not 0 <= mine_count <= n * n - len(seen))):
        raise ValueError("global mine count")

    hidden = set(range(n * n)) - seen
    around = tuple(_neighbors(n, index) & hidden for index, _ in clues)
    cells = tuple(sorted(set().union(*around)))
    if len(cells) != 6:
        return None
    bit_of = {cell: 1 << bit for bit, cell in enumerate(cells)}
    masks = tuple(sum(bit_of[cell] for cell in neighbors) for neighbors in around)
    use_total = mine_count is not None and len(hidden) == 6
    return ThreeClueInput(cells, masks, tuple(number for _, number in clues),
                          mine_count if use_total else 0, use_total)
