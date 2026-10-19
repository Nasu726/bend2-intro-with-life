"""Independent finite N x N Minesweeper rules oracle (NOT the Bend engine).

Used to test the planned variable-size Bend implementation. No toroidal
wrapping. The mine set is privileged game truth and is never returned by
public_view. This module does not prove Bend laws or no-guess solvability.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    n: int
    mines: frozenset[int]
    opened: tuple[tuple[int, int], ...] = ()
    flags: frozenset[int] = frozenset()
    phase: str = "Fresh"  # Fresh / Playing / Won / Lost


@dataclass(frozen=True)
class PublicView:
    n: int
    mine_count: int
    opened: tuple[tuple[int, int], ...]
    flags: frozenset[int]
    phase: str


def _size_ok(n: int) -> bool:
    return type(n) is int and 2 <= n <= 100


def index(n: int, x: int, y: int) -> int:
    """Row-major index, after checking both coordinates independently."""
    if not (_size_ok(n) and type(x) is int and type(y) is int
            and 0 <= x < n and 0 <= y < n):
        raise ValueError("invalid board coordinate")
    return y * n + x


def neighbors(n: int, i: int) -> tuple[int, ...]:
    if not (_size_ok(n) and type(i) is int and 0 <= i < n * n):
        raise ValueError("invalid cell index")
    x, y = i % n, i // n
    return tuple(yy * n + xx
                 for yy in range(max(0, y - 1), min(n, y + 2))
                 for xx in range(max(0, x - 1), min(n, x + 2))
                 if (xx, yy) != (x, y))


def storage_depth(n: int) -> int:
    """Minimum Bend Array.new depth for n*n logical cells."""
    if not _size_ok(n):
        raise ValueError("invalid board size")
    return (n * n - 1).bit_length()


def new_game(n: int, mines: frozenset[int]) -> State:
    if not _size_ok(n) or not isinstance(mines, frozenset):
        raise ValueError("invalid board setup")
    if (len(mines) >= n * n or
            any(type(i) is not int or not 0 <= i < n * n for i in mines)):
        raise ValueError("invalid mine placement")
    return State(n, mines)


def public_view(state: State) -> PublicView:
    return PublicView(state.n, len(state.mines), state.opened,
                      state.flags, state.phase)


def _valid_click(state: State, i: int) -> bool:
    return type(i) is int and 0 <= i < state.n * state.n


def mark(state: State, i: int) -> State:
    """Match the existing 4x4 GUI: flags before the first click are ignored."""
    if state.phase != "Playing" or not _valid_click(state, i):
        return state
    if i in dict(state.opened):
        return state
    flags = set(state.flags)
    if i in flags:
        flags.remove(i)
    else:
        flags.add(i)
    return State(state.n, state.mines, state.opened, frozenset(flags),
                 state.phase)


def click(state: State, i: int) -> State:
    """First-click relocation, safe zero flood, and terminal-state rules."""
    if state.phase in ("Won", "Lost") or not _valid_click(state, i):
        return state
    if i in state.flags or i in dict(state.opened):
        return state

    mines = state.mines
    if state.phase == "Fresh" and i in mines:
        # Deterministic relocation: first free cell, excluding clicked cell.
        destination = next(j for j in range(state.n * state.n)
                           if j not in mines and j != i)
        mines = frozenset((mines - {i}) | {destination})
    elif state.phase == "Playing" and i in mines:
        return State(state.n, mines, state.opened, state.flags, "Lost")

    opened = dict(state.opened)
    pending = [i]
    while pending:
        cell = pending.pop()
        if cell in opened or cell in state.flags:
            continue
        if cell in mines:
            raise AssertionError("flood reached a mine")
        count = sum(other in mines for other in neighbors(state.n, cell))
        opened[cell] = count
        if count == 0:
            pending.extend(other for other in neighbors(state.n, cell)
                           if other not in opened and other not in state.flags
                           and other not in mines)

    phase = ("Won" if len(opened) == state.n * state.n - len(mines)
             else "Playing")
    return State(state.n, mines, tuple(sorted(opened.items())),
                 state.flags, phase)
