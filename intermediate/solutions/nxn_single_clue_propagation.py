"""Sound *conditional* single-clue propagation from public Minesweeper numbers.

This is a Python reference bridge, not a Bend implementation or a general
solver. Only actual revealed numbers and independently certified evidence may
be passed in. Flags are not evidence. The returned sets include the supplied
certificates, and contain no unproved guesses. Inconsistent local constraints
raise ValueError; global satisfiability is NOT established by this routine.
"""


def _neighbors(n, cell):
    x, y = cell % n, cell // n
    return {yy * n + xx
            for yy in range(max(0, y - 1), min(n, y + 2))
            for xx in range(max(0, x - 1), min(n, x + 2))
            if yy * n + xx != cell}


def infer_single_clue_certainties(n, opened, certified_mines=(),
                                  certified_safe=()):
    """Return ``(certified_mines, certified_safe)`` after fixed-point closure.

    For each displayed clue, subtract neighboring certified mines. If its
    residual is zero, all remaining neighbors are safe; if the residual
    equals the number of remaining neighbors, all are mines. Iterate until
    neither set grows. Results are sound *provided* the displayed numbers
    and initial certificates are sound; they are not independent proofs.
    """
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("board size")
    try:
        clues = tuple(opened)
        mine_cells = tuple(certified_mines)
        safe_cells = tuple(certified_safe)
    except TypeError as exc:
        raise ValueError("opened clues or certified evidence") from exc

    shown = set()
    for clue in clues:
        if (not isinstance(clue, (tuple, list)) or len(clue) != 2 or
                type(clue[0]) is not int or not 0 <= clue[0] < n * n or
                type(clue[1]) is not int or not 0 <= clue[1] <= 8 or
                clue[0] in shown):
            raise ValueError("invalid or duplicate public clue")
        shown.add(clue[0])

    for label, cells in (("mine", mine_cells), ("safe", safe_cells)):
        if (any(type(cell) is not int or not 0 <= cell < n * n or
                cell in shown for cell in cells) or
                len(set(cells)) != len(cells)):
            raise ValueError("invalid or duplicate certified " + label)
    mines, safe = set(mine_cells), set(safe_cells)
    if mines & safe:
        raise ValueError("contradictory certificates")

    while True:
        next_mines, next_safe = set(), set()
        for cell, count in clues:
            around = _neighbors(n, cell)
            unknown = around - shown - mines - safe
            residual = count - len(around & mines)
            if not 0 <= residual <= len(unknown):
                raise ValueError("public clue contradicts certificates")
            if residual == 0:
                next_safe.update(unknown)
            if residual == len(unknown):
                next_mines.update(unknown)
        if (next_mines & (safe | next_safe) or
                next_safe & mines):
            raise ValueError("contradictory single-clue deductions")
        next_mines -= mines
        next_safe -= safe
        if not next_mines and not next_safe:
            return tuple(sorted(mines)), tuple(sorted(safe))
        mines.update(next_mines)
        safe.update(next_safe)
