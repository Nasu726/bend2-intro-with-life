"""Reference candidate screening for N x N no-guess Minesweeper.

The generator may inspect a candidate's mines; the inference engine never may.
A candidate is accepted only for the specified first click and deterministic
safe-click policy. This is Python reference code, not a Bend implementation.
"""
from dataclasses import dataclass

from nxn_board_oracle import click, new_game, public_view
from nxn_public_inference import infer


@dataclass(frozen=True)
class Replay:
    status: str  # accepted, first_mine, stuck, limit, contradiction
    clicks: tuple[int, ...] = ()
    opened_count: int = 0


def check_candidate(n, mines, first, max_frontier=18):
    """Replay only provably safe clicks; reject unresolved candidates.

    First-click mines are rejected rather than relocated, so an accepted
    candidate can be used unchanged in a game. No guessed clicks are made.
    """
    state = new_game(n, mines)
    if type(first) is not int or not 0 <= first < n*n:
        raise ValueError("first click")
    if type(max_frontier) is not int or not 0 <= max_frontier <= 24:
        raise ValueError("frontier limit")
    if first in mines:
        return Replay("first_mine")

    state = click(state, first)
    clicks = [first]
    while state.phase != "Won":
        view = public_view(state)
        result = infer(view.n, view.mine_count, view.opened, view.flags,
                       max_frontier=max_frontier)
        if result.status != "ok":
            return Replay(result.status, tuple(clicks), len(view.opened))
        if not result.safe:
            return Replay("stuck", tuple(clicks), len(view.opened))
        chosen = result.safe[0]  # Reproducible, public-information-only policy.
        following = click(state, chosen)
        if (following.phase == "Lost" or
                len(following.opened) <= len(state.opened)):
            raise AssertionError("public solver proposed an unsafe click")
        clicks.append(chosen)
        state = following
    return Replay("accepted", tuple(clicks), len(state.opened))
