"""Finite no-guess replay against the N x N *Python* game oracle.

This is a reference integration test, not a Bend implementation or a
proof of no-guess generation.  Only public_view is passed to infer().
The game engine alone knows the actual mine placement.
"""
from __future__ import annotations

from dataclasses import dataclass

import nxn_board_oracle as Game
from nxn_public_inference import infer


@dataclass(frozen=True)
class Replay:
    status: str  # won / stuck / limit / contradiction / budget
    clicks: tuple[int, ...]
    opened_count: int


def _start(n: int, mines: frozenset[int], first_click: int):
    game = Game.new_game(n, mines)
    if type(first_click) is not int or not 0 <= first_click < n*n:
        raise ValueError("invalid first click")
    return Game.click(game, first_click)


def _deduce(game, max_frontier: int):
    # Do not pass game.mines (the privileged truth) to the solver.
    public = Game.public_view(game)
    return infer(public.n, public.mine_count, public.opened,
                 flags=tuple(sorted(public.flags)), max_frontier=max_frontier)


def solve(n: int, mines: frozenset[int], first_click: int,
          *, max_frontier: int = 18, max_moves: int = 10000,
          selection: str = "highest") -> Replay:
    """Return a certified-by-the-Python-solver trace, or an explicit failure.

    First-click safety follows the game rule, not a deduction.  Every later
    click must be in the public solver's certain-safe set.  A search limit is
    not a contradiction, and an unfinished trace is not a no-guess board.
    """
    if type(max_moves) is not int or max_moves < 1:
        raise ValueError("invalid move budget")
    if type(selection) is not str or selection not in ("lowest", "highest"):
        raise ValueError("invalid safe-cell selection")
    if type(max_frontier) is not int or not 0 <= max_frontier <= 24:
        raise ValueError("invalid frontier limit")
    game = _start(n, mines, first_click)
    trace = [first_click]
    while game.phase == "Playing":
        if len(trace) >= max_moves:
            return Replay("budget", tuple(trace), len(game.opened))
        result = _deduce(game, max_frontier)
        if result.status != "ok":
            return Replay(result.status, tuple(trace), len(game.opened))
        if not result.safe:
            return Replay("stuck", tuple(trace), len(game.opened))
        # A safe move is guaranteed; which safe move to choose affects
        # flood expansion and therefore the future frontier search cost.
        next_click = (min(result.safe) if selection == "lowest"
                      else max(result.safe))
        game = Game.click(game, next_click)
        trace.append(next_click)
        if game.phase == "Lost":
            raise AssertionError("public inference certified a mined cell")
    if game.phase != "Won":
        raise AssertionError("unexpected terminal state")
    return Replay("won", tuple(trace), len(game.opened))


def verify(n: int, mines: frozenset[int], clicks: tuple[int, ...],
           *, max_frontier: int = 18) -> bool:
    """Replay an external click certificate; reject guesses and partial wins.

    The verifier shares the public inference algorithm with solve(), so its
    acceptance is NOT an independent proof of the solver's soundness.
    """
    if type(max_frontier) is not int or not 0 <= max_frontier <= 24:
        raise ValueError("invalid frontier limit")
    if not isinstance(clicks, tuple) or not clicks:
        raise ValueError("invalid click certificate")
    game = _start(n, mines, clicks[0])
    if any(type(i) is not int or not 0 <= i < n*n for i in clicks[1:]):
        raise ValueError("invalid click certificate")
    for move in clicks[1:]:
        if game.phase != "Playing":
            return False
        result = _deduce(game, max_frontier)
        if result.status != "ok" or move not in result.safe:
            return False
        game = Game.click(game, move)
        if game.phase == "Lost":
            raise AssertionError("certified click reached a mine")
    return game.phase == "Won"


if __name__ == "__main__":
    example_mines = frozenset(range(50, 60))
    successful = solve(10, example_mines, 0)
    print("highest:", successful)
    print("certificate:", verify(10, example_mines, successful.clicks))
    print("lowest:", solve(10, example_mines, 0, selection="lowest"))
