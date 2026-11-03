"""Generate replayable public-only single-clue certificates.

The generator cross-checks the reference propagation solver; the independent
checker lives in nxn_single_clue_checker and does not import either one.
Flags and hidden mine truth are never inputs. This is conditional local
reasoning, not a global satisfiability proof.
"""
from nxn_single_clue_checker import Deduction, _input, _forced, replay
from nxn_single_clue_propagation import infer_single_clue_certainties


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


