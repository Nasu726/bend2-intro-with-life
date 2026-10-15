#!/usr/bin/env python3
"""Independent Python oracle for the educational 8x8 toroidal Life program.
This checks the mathematical rule, not the Bend compiler.
"""
from __future__ import annotations
from dataclasses import dataclass

SIZE = 8
GLIDER = {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}


def step(cells: set[tuple[int, int]], size: int = SIZE) -> set[tuple[int, int]]:
    result = set()
    for y in range(size):
        for x in range(size):
            n = sum(((x + dx) % size, (y + dy) % size) in cells
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                    if dx != 0 or dy != 0)
            if n == 3 or (n == 2 and (x, y) in cells):
                result.add((x, y))
    return result


def render(cells: set[tuple[int, int]], size: int = SIZE) -> str:
    return "\n".join("".join("1" if (x, y) in cells else "0" for x in range(size))
                     for y in range(size))


def transcript(generations: int = 5) -> str:
    board = set(GLIDER)
    parts = []
    for generation in range(generations):
        parts.append(f"generation {generation}\n{render(board)}\n\n")
        board = step(board)
    parts.append("done\n")
    return "".join(parts)


if __name__ == '__main__':
    print(transcript(), end='')
