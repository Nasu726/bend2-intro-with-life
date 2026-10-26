"""Replayable, public-only certificates for N x N single-clue propagation.

The generator needs only public numbers and independently certified cells;
flags and hidden mine truth are never inputs. Verification does not call the
propagation solver: every move is checked from the current public evidence.
This proves conditional local deduction, NOT global board satisfiability.
"""
from dataclasses import dataclass

from nxn_single_clue_propagation import infer_single_clue_certainties


@dataclass(frozen=True)
class Deduction:
    clue: int
    mines: tuple[int, ...] = ()
    safe: tuple[int, ...] = ()


def _neighbors(n, cell):
    x, y = cell % n, cell // n
    return {row * n + col
            for row in range(max(0, y - 1), min(n, y + 2))
            for col in range(max(0, x - 1), min(n, x + 2))
            if row * n + col != cell}


def _input(n, opened, certified_mines, certified_safe):
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("board size")
    try:
        clues = tuple(opened)
        mines = tuple(certified_mines)
        safe = tuple(certified_safe)
    except TypeError as e:
        raise ValueError("noniterable evidence") from e
    public = {}
    for pair in clues:
        if (not isinstance(pair, (tuple, list)) or len(pair) != 2 or
                type(pair[0]) is not int or type(pair[1]) is not int or
                not 0 <= pair[0] < n*n or not 0 <= pair[1] <= 8 or
                pair[0] in public):
            raise ValueError("invalid public clue")
        public[pair[0]] = pair[1]
    for group in (mines, safe):
        if (any(type(cell) is not int or not 0 <= cell < n*n or
                cell in public for cell in group) or len(set(group)) != len(group)):
            raise ValueError("invalid certified cells")
    if set(mines) & set(safe):
        raise ValueError("conflicting certificates")
    return public, set(mines), set(safe)


def _forced(n, public, mines, safe, cell):
    around = _neighbors(n, cell)
    unknown = around - public.keys() - mines - safe
    residual = public[cell] - len(around & mines)
    if not 0 <= residual <= len(unknown):
        raise ValueError("inconsistent public clue and certificates")
    if residual == 0:
        return (), tuple(sorted(unknown))
    if residual == len(unknown):
        return tuple(sorted(unknown)), ()
    return (), ()


def certify(n, opened, certified_mines=(), certified_safe=()):
    """Return (mines, safe, proof steps) in deterministic clue-index order."""
    public, mines, safe = _input(n, opened, certified_mines, certified_safe)
    # _input consumes one-shot iterables. Preserve their validated values for
    # the independent round-based comparison instead of reading them again.
    initial_clues = tuple(sorted(public.items()))
    initial_mines = tuple(sorted(mines))
    initial_safe = tuple(sorted(safe))
    steps = []
    while True:
        changed = False
        for cell in sorted(public):
            added_mines, added_safe = _forced(n, public, mines, safe, cell)
            if added_mines or added_safe:
                steps.append(Deduction(cell, added_mines, added_safe))
                mines.update(added_mines)
                safe.update(added_safe)
                changed = True
        if not changed:
            break
    # Independent simultaneous-round implementation must reach same closure.
    expected = infer_single_clue_certainties(
        n, initial_clues, initial_mines, initial_safe)
    outcome = tuple(sorted(mines)), tuple(sorted(safe))
    if outcome != expected:
        raise AssertionError("certificate generator and reference disagree")
    return *outcome, tuple(steps)


def replay(n, opened, certified_mines, certified_safe, steps):
    """Verify individual steps and final fixed point without calling the solver.

    Rejects fabricated deductions, duplicated cells, missing steps and
    locally inconsistent evidence; does not establish global satisfiability.
    """
    public, mines, safe = _input(n, opened, certified_mines, certified_safe)
    try:
        evidence = tuple(steps)
    except TypeError as e:
        raise ValueError("noniterable certificate") from e
    for step in evidence:
        if not isinstance(step, Deduction) or type(step.clue) is not int or step.clue not in public:
            raise ValueError("invalid proof step")
        if (not isinstance(step.mines, tuple) or not isinstance(step.safe, tuple) or
                not step.mines and not step.safe):
            raise ValueError("empty or malformed proof step")
        for group in (step.mines, step.safe):
            if (any(type(cell) is not int for cell in group) or
                    tuple(sorted(set(group))) != group):
                raise ValueError("unsorted or duplicated proof cells")
        allowed_mines, allowed_safe = _forced(n, public, mines, safe, step.clue)
        if (not set(step.mines) <= set(allowed_mines) or
                not set(step.safe) <= set(allowed_safe)):
            raise ValueError("unproved deduction")
        mines.update(step.mines)
        safe.update(step.safe)
    for cell in public:
        needed_mines, needed_safe = _forced(n, public, mines, safe, cell)
        if needed_mines or needed_safe:
            raise ValueError("incomplete fixed-point certificate")
    return tuple(sorted(mines)), tuple(sorted(safe))
