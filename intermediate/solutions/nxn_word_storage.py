"""Independent N x N bit-packed mine oracle; never expose to a solver.

The storage contract is a tuple of ceil(n*n/32) unsigned 32-bit words.
Bits beyond the n*n logical cells must be zero. This is a Python reference
for a future Bend engine, not an implementation or proof of that engine.
"""

WORD_BITS = 32
WORD_MAX = (1 << WORD_BITS) - 1


def _cells(n):
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("size")
    return n * n


def validate(n, words):
    """Reject malformed words, including nonzero bits in the padding area."""
    cells = _cells(n)
    length = (cells + WORD_BITS - 1) // WORD_BITS
    if (type(words) is not tuple or len(words) != length or
            any(type(w) is not int or not 0 <= w <= WORD_MAX for w in words)):
        raise ValueError("words")
    used = cells % WORD_BITS
    if used and words[-1] >> used:
        raise ValueError("padding")
    return words


def pack(n, mines):
    cells = _cells(n)
    words = [0] * ((cells + WORD_BITS - 1) // WORD_BITS)
    try:
        iterator = iter(mines)
    except TypeError as exc:
        raise ValueError("mines") from exc
    for i in iterator:
        if type(i) is not int or not 0 <= i < cells:
            raise ValueError("cell")
        words[i // WORD_BITS] |= 1 << (i % WORD_BITS)
    return tuple(words)


def has(n, words, i):
    validate(n, words)
    return (type(i) is int and 0 <= i < n*n and
            bool(words[i // WORD_BITS] & (1 << (i % WORD_BITS))))


def set_cell(n, words, i, value):
    """Return updated immutable words; reject padding and invalid indices."""
    validate(n, words)
    if type(i) is not int or not 0 <= i < n*n or type(value) is not bool:
        raise ValueError("cell/value")
    slot, offset = divmod(i, WORD_BITS)
    result = list(words)
    if value:
        result[slot] |= 1 << offset
    else:
        result[slot] &= WORD_MAX ^ (1 << offset)
    return tuple(result)


def unpack(n, words):
    validate(n, words)
    return frozenset(i for i in range(n*n)
                     if words[i // WORD_BITS] & (1 << (i % WORD_BITS)))


def count(n, words):
    validate(n, words)
    return sum(word.bit_count() for word in words)


def relocate_first_click(n, words, clicked):
    """Move a first-click mine to the lowest free cell, preserving mine count.

    Reject invalid clicks and full boards. If clicked is safe, keep the exact
    immutable words. This is an internal game operation, not public solver data.
    """
    validate(n, words)
    if type(clicked) is not int or not 0 <= clicked < n*n:
        raise ValueError("clicked")
    if count(n, words) == n*n:
        raise ValueError("full board")
    if not has(n, words, clicked):
        return words
    replacement = next(i for i in range(n*n)
                       if not (words[i // WORD_BITS] & (1 << (i % WORD_BITS))))
    return set_cell(n, set_cell(n, words, clicked, False), replacement, True)

def adjacent_count(n, words, i):
    """Count mines in the at-most-eight non-wrapping neighboring cells.

    Privileged game logic only: never pass the true mine words to a
    public-information solver. Reject invalid storage and cell indices.
    """
    validate(n, words)
    if type(i) is not int or not 0 <= i < n*n:
        raise ValueError("cell")
    y, x = divmod(i, n)
    total = 0
    for yy in range(max(0, y-1), min(n, y+2)):
        for xx in range(max(0, x-1), min(n, x+2)):
            if xx == x and yy == y:
                continue
            j = yy*n + xx
            total += (words[j//WORD_BITS] >> (j%WORD_BITS)) & 1
    return total
