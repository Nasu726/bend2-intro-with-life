"""Validate the textual Nat returned by the Bend elapsed-clock example.

This validates output syntax only; IO.sleep and IO.now do not promise a
specific elapsed duration or a positive measurement on every platform.
"""
import re


def is_nat_decimal(output: str) -> bool:
    """Accept canonical ASCII Nat.show output, including zero."""
    return isinstance(output, str) and re.fullmatch(r"(?:0|[1-9][0-9]*)", output) is not None
