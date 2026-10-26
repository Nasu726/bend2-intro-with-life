"""Public-clue adapter for the Bend six-bit, three-constraint kernel.

This produces *inputs*, not a proof or a general N x N solver. It never
accepts the true mine layout or treats a player's flag as known evidence.
Only separately certified mines may be supplied to subtract from clues.
Separately certified safe cells may be excluded from the frontier without
changing any clue's residual count. Neither kind of evidence is a player flag.
The Bend kernel always enumerates six bits; other frontier sizes are skipped.
"""
from dataclasses import dataclass
from itertools import combinations


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


def from_public_clues(n, opened, mine_count=None, certified_mines=(),
                      certified_safe=()):
    """Build one six-cell request from exactly three public clues, if possible.

    ``certified_mines`` and ``certified_safe`` must be independently proved,
    not inferred from unverified player flags. A global mine total is used
    only when the six unknown cells exhaust the remaining board after both
    kinds of certified evidence are removed.
    """
    try:
        clues = tuple(opened)
    except TypeError as exc:
        raise ValueError("opened clues") from exc
    if len(clues) != 3:
        raise ValueError("exactly three public clues required")
    return next(iter(from_public_board(n, clues, mine_count,
                                       certified_mines=certified_mines,
                                       certified_safe=certified_safe)), None)


def from_public_board(n, opened, mine_count=None, certified_mines=(),
                      certified_safe=()):
    """Enumerate supported three-clue Bend requests from a public board.

    Opened cells, certified mines and certified safe cells are excluded from
    the six unknown bits. Each clue's count is reduced only by neighboring
    certified mines. Player flags are not certified evidence.
    If the six cells are only a subset of remaining unknown cells, a global
    mine total cannot be used in the local Bend kernel.
    """
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("board size")
    try:
        clues = tuple(opened)
        certified = tuple(certified_mines)
        safe = tuple(certified_safe)
    except TypeError as exc:
        raise ValueError("opened clues or certified evidence") from exc
    if not 3 <= len(clues) <= 24:
        raise ValueError("three to 24 public clues required")
    shown = set()
    for item in clues:
        if (not isinstance(item, (tuple, list)) or len(item) != 2 or
                type(item[0]) is not int or not 0 <= item[0] < n * n or
                type(item[1]) is not int or not 0 <= item[1] <= 8 or
                item[0] in shown):
            raise ValueError("invalid or duplicate public clue")
        shown.add(item[0])
    if (any(type(cell) is not int or not 0 <= cell < n*n or cell in shown
            for cell in certified) or len(set(certified)) != len(certified)):
        raise ValueError("invalid or duplicate certified mine")
    known = set(certified)
    if (any(type(cell) is not int or not 0 <= cell < n*n or
            cell in shown or cell in known for cell in safe) or
            len(set(safe)) != len(safe)):
        raise ValueError("invalid or duplicate certified safe cell")
    unknown = set(range(n*n)) - shown - known - set(safe)
    if (mine_count is not None and
            (type(mine_count) is not int or
             not len(known) <= mine_count <= len(unknown) + len(known))):
        raise ValueError("global mine count")

    residuals = {}
    for cell, number in clues:
        residual = number - len(_neighbors(n, cell) & known)
        if residual < 0:
            raise ValueError("certified mines contradict public clue")
        residuals[cell] = residual

    use_total = mine_count is not None and len(unknown) == 6
    remaining_total = mine_count - len(known) if use_total else 0
    requests = []
    for triple in combinations(clues, 3):
        around = tuple(_neighbors(n, cell) & unknown for cell, _ in triple)
        cells = tuple(sorted(set().union(*around)))
        if len(cells) != 6:
            continue
        bit_of = {cell: 1 << bit for bit, cell in enumerate(cells)}
        masks = tuple(sum(bit_of[cell] for cell in neighbors)
                      for neighbors in around)
        requests.append(ThreeClueInput(
            cells, masks, tuple(residuals[cell] for cell, _ in triple),
            remaining_total, use_total))
    return tuple(requests)


def combine_public_decisions(pairs):
    """Union sound forced cells from separately evaluated Bend requests.

    A decision is None for Inconsistent, otherwise (safe, mines, models) from
    Forced. A conflict/inconsistent triple returns None, but absence of a
    conflict does NOT prove the full public board globally consistent.
    Candidate counts across overlapping triples must never be added.
    """
    safe, mines = set(), set()
    for request, decision in pairs:
        if not isinstance(request, ThreeClueInput):
            raise ValueError("invalid kernel request")
        if decision is None:
            return None
        if (not isinstance(decision, (tuple, list)) or len(decision) != 3 or
                any(type(value) is not int for value in decision)):
            raise ValueError("invalid kernel decision")
        safe_bits, mine_bits, models = decision
        if (not 0 <= safe_bits <= 63 or not 0 <= mine_bits <= 63 or
                models <= 0 or safe_bits & mine_bits):
            raise ValueError("invalid forced masks or model count")
        for bit, cell in enumerate(request.cells):
            if safe_bits & (1 << bit):
                safe.add(cell)
            if mine_bits & (1 << bit):
                mines.add(cell)
    if safe & mines:
        return None
    return tuple(sorted(safe)), tuple(sorted(mines))
