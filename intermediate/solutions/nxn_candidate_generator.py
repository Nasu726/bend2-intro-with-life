"""Bounded, deterministic N x N no-guess candidate search (Python reference).

This module is not a Bend implementation. It enumerates candidate mine sets
with a *safe fixed first click*, then delegates every acceptance decision to
nxn_noguess_replay.check_candidate. That replay feeds only public clues to
its solver; true mine positions are confined to candidate construction and
simulation. An accepted certificate is for one first click and one fixed
safe-click policy, not for every possible way of playing.
"""
from dataclasses import dataclass
from itertools import combinations, islice
from math import comb

from nxn_noguess_replay import check_candidate


@dataclass(frozen=True)
class Certificate:
    mines: tuple[int, ...]
    clicks: tuple[int, ...]
    opened_count: int


@dataclass(frozen=True)
class Generation:
    status: str  # accepted, budget, inconclusive, no_match
    examined: int
    possible: int
    stuck: int
    limited: int
    certificate: Certificate | None = None


def generate(n, mine_count, first, max_candidates=120, max_frontier=18):
    """Find a certified candidate by bounded lexicographic enumeration.

    ``budget``: candidate count truncated before exhaustive search.
    ``inconclusive``: all candidates tried, but at least one hit the solver
      frontier limit, so its solvability is unknown.
    ``no_match``: all candidates tried; none was accepted under the fixed
      public-safe-click policy. This does not prove no other policy can win.

    The first cell is excluded from mine placements. No mine relocation is
    performed when a candidate is screened, and no candidate is accepted
    without an actual replay reaching Won.
    """
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("board size")
    cells = n * n
    if (type(mine_count) is not int or not 0 <= mine_count < cells or
            type(first) is not int or not 0 <= first < cells):
        raise ValueError("mine count or first click")
    if type(max_candidates) is not int or not 1 <= max_candidates <= 100000:
        raise ValueError("candidate budget")
    if type(max_frontier) is not int or not 0 <= max_frontier <= 24:
        raise ValueError("frontier limit")

    choices = tuple(i for i in range(cells) if i != first)
    possible = comb(cells - 1, mine_count)
    stuck = limited = examined = 0
    for placement in islice(combinations(choices, mine_count), max_candidates):
        replay = check_candidate(n, frozenset(placement), first,
                                 max_frontier=max_frontier)
        examined += 1
        if replay.status == "accepted":
            return Generation("accepted", examined, possible, stuck, limited,
                              Certificate(placement, replay.clicks,
                                          replay.opened_count))
        if replay.status == "stuck":
            stuck += 1
        elif replay.status == "limit":
            limited += 1
        else:
            # A real candidate's published clues cannot contradict its own
            # board, and first-click mines were explicitly excluded.
            raise AssertionError(f"unexpected replay status: {replay.status}")

    status = ("budget" if examined < possible else
              "inconclusive" if limited else "no_match")
    return Generation(status, examined, possible, stuck, limited)
