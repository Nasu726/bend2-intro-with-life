"""Validate the textual Nat returned by the Bend elapsed-clock example.

This validates output syntax only; IO.sleep and IO.now do not promise a
specific elapsed duration or a positive measurement on every platform.
"""
import re


def is_nat_decimal(output: str) -> bool:
    """Accept canonical ASCII Nat.show output, including zero."""
    return isinstance(output, str) and re.fullmatch(r"(?:0|[1-9][0-9]*)", output) is not None


def is_nat_stdout(stdout: str) -> bool:
    """Accept one canonical Nat value and at most one platform line ending.

    Check the complete process stdout: strip() would hide extra output.
    """
    if not isinstance(stdout, str):
        return False
    if stdout.endswith("\r\n"):
        stdout = stdout[:-2]
    elif stdout.endswith("\n"):
        stdout = stdout[:-1]
    return is_nat_decimal(stdout)
