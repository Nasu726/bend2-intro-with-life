"""Independent N x N bit-packed mine oracle; never expose to a solver."""


def pack(n, mines):
    if type(n) is not int or not 2 <= n <= 100:
        raise ValueError("size")
    if any(type(i) is not int or not 0 <= i < n*n for i in mines):
        raise ValueError("cell")
    words = [0] * ((n*n + 31)//32)
    for i in mines:
        words[i//32] |= 1 << (i % 32)
    return tuple(words)


def has(n, words, i):
    return type(i) is int and 0 <= i < n*n and bool(words[i//32] & (1 << (i % 32)))


def unpack(n, words):
    return frozenset(i for i in range(n*n) if has(n, words, i))
