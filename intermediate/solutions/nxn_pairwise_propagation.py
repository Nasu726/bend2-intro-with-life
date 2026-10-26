"""Public-only single- and two-clue fixed-point inference for N x N Minesweeper.

This Python reference combines the existing single-clue rule with exact
intersection bounds for pairs of nearby public clues. Inputs must be genuine
revealed numbers and independently certified cells; player flags and hidden
mine layouts are never evidence. It is not a complete frontier solver and a
locally consistent result need not admit a global mine configuration.
"""
from nxn_single_clue_propagation import infer_single_clue_certainties, _neighbors


def _pair_deductions(a, ra, b, rb):
    """Return forced (mines, safe) or raise on an impossible pair.

    X=A\\B, I=A&B, Y=B\\A. If t mines lie in I, then
    max(0, ra-|X|, rb-|Y|) <= t <= min(|I|, ra, rb).
    """
    intersection = a & b
    if not intersection:
        return set(), set()
    x, y = a - b, b - a
    low = max(0, ra - len(x), rb - len(y))
    high = min(len(intersection), ra, rb)
    if low > high:
        raise ValueError("public clue pair contradicts certificates")
    mines, safe = set(), set()
    for region, minimum, maximum in (
        (intersection, low, high),
        (x, ra - high, ra - low),
        (y, rb - high, rb - low),
    ):
        if minimum == len(region):
            mines.update(region)
        if maximum == 0:
            safe.update(region)
    return mines, safe


def infer_pairwise_clue_certainties(n, opened, certified_mines=(),
                                    certified_safe=()):
    """Return sound certified (mines, safe) after single/pair closure.

    Only clue pairs within Chebyshev distance two can share a neighbor;
    scanning those pairs avoids quadratic comparisons on large boards.
    The fixed point is sound conditional on genuine public clues and valid
    initial certificates, but it is not an independent global proof.
    """
    try:
        clues = tuple(opened)
        initial_mines = tuple(certified_mines)
        initial_safe = tuple(certified_safe)
    except TypeError as exc:
        raise ValueError("opened clues or certified evidence") from exc

    mines, safe = infer_single_clue_certainties(
        n, clues, initial_mines, initial_safe)
    clue_by_index = dict(clues)
    shown = set(clue_by_index)
    while True:
        mine_set, safe_set = set(mines), set(safe)
        constraints = {}
        for cell, count in clues:
            around = _neighbors(n, cell)
            unknown = around - shown - mine_set - safe_set
            residual = count - len(around & mine_set)
            # The single-clue closure already checked this, but checking
            # here makes the pairwise routine's invariant explicit.
            if not 0 <= residual <= len(unknown):
                raise ValueError("public clue contradicts certificates")
            constraints[cell] = (unknown, residual)

        new_mines, new_safe = set(), set()
        for cell in clue_by_index:
            x, y = cell % n, cell // n
            a, ra = constraints[cell]
            for yy in range(max(0, y - 2), min(n, y + 3)):
                for xx in range(max(0, x - 2), min(n, x + 3)):
                    other = yy * n + xx
                    if other <= cell or other not in clue_by_index:
                        continue
                    b, rb = constraints[other]
                    pair_mines, pair_safe = _pair_deductions(a, ra, b, rb)
                    new_mines.update(pair_mines)
                    new_safe.update(pair_safe)
        if (new_mines & (safe_set | new_safe) or
                new_safe & mine_set):
            raise ValueError("contradictory pairwise deductions")
        new_mines -= mine_set
        new_safe -= safe_set
        if not new_mines and not new_safe:
            return mines, safe
        mines, safe = infer_single_clue_certainties(
            n, clues, mine_set | new_mines, safe_set | new_safe)
