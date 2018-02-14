"""Defines a variety of helper functions."""

from enum import Flag
from typing import Any

BASIC_TYPES = {
    bool,
    bytes,
    float,
    int,
    str,
}


def enum_from_set(flags: Flag, options: set) -> Flag:
    """Convert a set of strings to a bitwise flag instance.

    Example:

        from enum import Flag, auto
        from anansi.utils import enum_from_set

        class MyFlag(Flag):
            A = auto()
            B = auto()

        assert enum_from_set(MyFlag, {'A', 'B'}) == MyFlag.A | MyFlag.B
        assert enum_from_set(MyFlag, {}) == MyFlag(0)
        assert enum_from_set(MyFlag, {'A'}) == MyFlag.A
    """
    out = flags(0)
    for option in options:
        out |= getattr(flags, option)
    return out


def is_equal(a: Any, b: Any) -> bool:
    """Return whether or not a and b are equal by equality and identity."""
    if type(a) is type(b) and type(a) in BASIC_TYPES:
        return a == b
    return a is b
