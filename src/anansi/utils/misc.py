"""Miscellaneous utilities."""
from typing import Any

BASIC_TYPES = {
    bool,
    bytes,
    float,
    int,
    str,
}


def is_equal(a: Any, b: Any) -> bool:
    """Return whether or not a and b are equal by equality and identity."""
    if type(a) is type(b) and type(a) in BASIC_TYPES:
        return a == b
    return a is b
