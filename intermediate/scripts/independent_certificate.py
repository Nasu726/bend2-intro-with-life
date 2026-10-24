"""Independently verify the *publicly forced* clicks in a Bend certificate.

No imports from the Bend engine or Python no-guess reference are used here.
This checker deliberately handles only 4x4 boards containing two mines.
"""
from itertools import combinations

CELLS = frozenset(range(16))


def adjacent(index):
    x, y = index % 4, index // 4
    return frozenset(j for j in CELLS if j != index
                     and abs(x - j % 4) <= 1 and abs(y - j // 4) <= 1)


def verify_certificate(mask, clicks, first_click=0):
    """Raise ValueError for a false, guessed, or incomplete certificate.

    The declared first click and its neighbors must contain no mines.
    Subsequent clicks must be forced safe by public clues alone.
    """
    if type(mask) is not int or mask < 0 or mask >= (1 << 16):
        raise ValueError("invalid 16-bit mine mask")
    mines = frozenset(i for i in CELLS if mask & (1 << i))
    if len(mines) != 2:
        raise ValueError("expected exactly two mines")
    if type(first_click) is not int or first_click not in CELLS:
        raise ValueError("invalid first click")
    # Reject booleans and malformed containers before using indexing or sets.
    # In Python, False == 0 and True == 1, but neither is a cell index.
    if not isinstance(clicks, (list, tuple)):
        raise ValueError("click sequence must be a list or tuple")
    if any(type(i) is not int or i not in CELLS for i in clicks):
        raise ValueError("click outside 4x4 board")
    if not clicks or clicks[0] != first_click:
        raise ValueError("certificate does not start at declared first click")
    if len(set(clicks)) != len(clicks):
        raise ValueError("repeated click")
    if mines & ({first_click} | adjacent(first_click)):
        raise ValueError("first click is not protected")

    opened = {}
    for step, click in enumerate(clicks):
        if click in opened:
            raise ValueError("clicked already-open cell")
        if click in mines:
            raise ValueError("clicked a mine")
        if step:
            hidden = CELLS - opened.keys()
            models = [frozenset(pair) for pair in combinations(sorted(hidden), 2)
                      if all(len(adjacent(i) & set(pair)) == clue
                             for i, clue in opened.items())]
            if not models:
                raise ValueError("public numbers admit no mine layout")
            if any(click in candidate for candidate in models):
                raise ValueError("click is a guess, not forced safe")

        # Independent FIFO zero expansion; adjacent numbers open but do not expand.
        queue = [click]
        while queue:
            i = queue.pop(0)
            if i in opened:
                continue
            if i in mines:
                raise ValueError("zero flood reached a mine")
            clue = len(adjacent(i) & mines)
            opened[i] = clue
            if clue == 0:
                queue.extend(sorted(adjacent(i) - opened.keys()))
    if set(opened) != CELLS - mines:
        raise ValueError("certificate did not reach a win")
    return tuple(sorted(opened.items()))
