"""Bounded N x N no-guess candidate generation and replayable certificates.

Python reference only. The solver sees Visible (opened clues and mine count),
never the candidate's hidden mine locations. A candidate is accepted only
when every post-first-click move is forced safe and all safe cells are opened.
No claim is made for rejected boards, other click orders, or Bend's GUI.
"""
from __future__ import annotations

from dataclasses import dataclass
import random

from noguess_reference import GenerationFailed, SearchLimit, Visible, expose, neighbors
from nxn_frontier_solver import provably_safe_frontier, verify_no_guess_frontier
from nxn_certificate_audit import audit_certificate


@dataclass(frozen=True)
class Certificate:
    width: int
    height: int
    mine_count: int
    first_click: int
    mines: frozenset[int]
    clicks: tuple[int, ...]


def _request(width, height, mine_count, first_click, node_limit):
    if (type(width) is not int or type(height) is not int
            or width < 1 or height < 1 or width * height > 10_000
            or type(mine_count) is not int or not 0 <= mine_count < width * height
            or type(first_click) is not int
            or not 0 <= first_click < width * height
            or type(node_limit) is not int or node_limit < 1):
        raise ValueError("invalid board, first click or search budget")


def verify_certificate(cert: Certificate, node_limit: int = 200_000) -> bool:
    """Fail closed on malformed, incomplete, guessed or uncheckable traces.

    The candidate truth is used only by expose, the game-side operation.
    The inference function receives the public Visible state exclusively.
    """
    if not isinstance(cert, Certificate):
        return False
    try:
        _request(cert.width, cert.height, cert.mine_count,
                 cert.first_click, node_limit)
        cells = cert.width * cert.height
        if (not isinstance(cert.mines, frozenset)
                or len(cert.mines) != cert.mine_count
                or any(type(i) is not int or not 0 <= i < cells
                       for i in cert.mines)
                or not isinstance(cert.clicks, tuple)
                or not cert.clicks or cert.clicks[0] != cert.first_click
                or any(type(i) is not int or not 0 <= i < cells
                       for i in cert.clicks)
                or cert.first_click in cert.mines):
            return False
        view = Visible(cert.width, cert.height, cert.mine_count, ())
        for position, click in enumerate(cert.clicks):
            if click in dict(view.opened):
                return False  # Replaying a previously opened cell is not progress.
            if position:
                safe = provably_safe_frontier(view, node_limit=node_limit)
                if click not in safe:
                    return False
            view = expose(cert.mines, view, click)
            if len(view.opened) == cells - cert.mine_count:
                return position == len(cert.clicks) - 1
        return False
    except (ValueError, SearchLimit, AssertionError):
        return False


def generate_no_guess_frontier(width: int, height: int, mine_count: int,
                               first_click: int, seed: int, attempts: int = 100,
                               node_limit: int = 200_000) -> Certificate:
    """Sample reproducible zero-first-click boards; accept only with a trace.

    Search exhaustion raises GenerationFailed, never a guessed fallback.
    This does not guarantee that a given request will find a board.
    """
    _request(width, height, mine_count, first_click, node_limit)
    if type(seed) is not int or type(attempts) is not int or attempts < 1:
        raise ValueError("seed must be int and attempts must be positive")
    protected = {first_click, *neighbors(first_click, width, height)}
    allowed = sorted(set(range(width * height)) - protected)
    if mine_count > len(allowed):
        raise ValueError("too many mines to protect the first click and its neighbors")
    rng = random.Random(seed)
    for _ in range(attempts):
        mines = frozenset(rng.sample(allowed, mine_count))
        trace = verify_no_guess_frontier(width, height, mines, first_click,
                                         node_limit=node_limit)
        if trace is None:
            continue
        cert = Certificate(width, height, mine_count, first_click, mines, trace)
        if not verify_certificate(cert, node_limit=node_limit):
            raise AssertionError("solver produced an invalid replay certificate")
        if not audit_certificate(cert, node_limit=node_limit):
            raise AssertionError("independent replay audit rejected the certificate")
        return cert
    raise GenerationFailed(f"no certified board in {attempts} attempts")
