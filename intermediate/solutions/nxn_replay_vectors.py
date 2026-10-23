"""Deterministic public-state replay vectors for the future N x N Bend engine.

This is a Python fixture producer, NOT the Bend engine or a no-guess solver.
Hidden mines are used only to simulate clicks; ReplayFrame contains only
observable cells, clues and the phase. Call the independent certificate audit
separately before claiming that a click sequence needs no guessing.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayFrame:
    click: int
    newly_opened: tuple[tuple[int, int], ...]
    opened: tuple[tuple[int, int], ...]
    opened_words: tuple[int, ...]
    phase: str


def _neighbors(n: int, cell: int) -> tuple[int, ...]:
    x, y = cell % n, cell // n
    return tuple(yy * n + xx
                 for yy in range(max(0, y - 1), min(n, y + 2))
                 for xx in range(max(0, x - 1), min(n, x + 2))
                 if (xx, yy) != (x, y))


def replay_vectors(n: int, mines: frozenset[int],
                   clicks: tuple[int, ...]) -> tuple[ReplayFrame, ...]:
    """Replay a complete safe trace; reject mines, repeated moves and gaps.

    The first click must already be safe: this models a preselected no-guess
    board, not the game's first-click relocation operation. Zero-flood uses
    non-toroidal eight-neighborhoods and stops at numbered boundary cells.
    """
    if (type(n) is not int or not 2 <= n <= 100
            or type(mines) is not frozenset or len(mines) >= n * n
            or any(type(i) is not int or not 0 <= i < n * n for i in mines)
            or type(clicks) is not tuple or not clicks
            or any(type(i) is not int or not 0 <= i < n * n for i in clicks)):
        raise ValueError("invalid N x N replay fixture")
    opened: dict[int, int] = {}
    frames = []
    for position, click in enumerate(clicks):
        if click in mines or click in opened:
            raise ValueError("unsafe or redundant click")
        previous = set(opened)
        pending = [click]
        while pending:
            cell = pending.pop()
            if cell in opened:
                continue
            if cell in mines:
                raise AssertionError("zero-flood reached a mine")
            near = _neighbors(n, cell)
            clue = sum(other in mines for other in near)
            opened[cell] = clue
            if clue == 0:
                pending.extend(other for other in near
                               if other not in opened and other not in mines)
        pairs = tuple(sorted(opened.items()))
        new = tuple((i, clue) for i, clue in pairs if i not in previous)
        words = [0] * ((n * n + 31) // 32)
        for i in opened:
            words[i // 32] |= 1 << (i % 32)
        won = len(opened) == n * n - len(mines)
        if won and position != len(clicks) - 1:
            raise ValueError("clicks continue after victory")
        frames.append(ReplayFrame(click, new, pairs, tuple(words),
                                  "Won" if won else "Playing"))
    if frames[-1].phase != "Won":
        raise ValueError("incomplete safe-click trace")
    return tuple(frames)


def render_replay(frames: tuple[ReplayFrame, ...]) -> str:
    """Stable line-oriented contract for future Bend-vs-Python CI comparison.

    This output contains only public state, never the true mine words.
    """
    if not frames:
        raise ValueError("empty replay")
    return "\n".join(
        f"step={step};click={frame.click};opened={len(frame.opened)};"
        f"phase={frame.phase};words={','.join(f'{w:08x}' for w in frame.opened_words)};"
        f"new={','.join(f'{i}:{clue}' for i, clue in frame.newly_opened)}"
        for step, frame in enumerate(frames)) + "\n"
