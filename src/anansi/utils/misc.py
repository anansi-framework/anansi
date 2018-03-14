"""Miscellaneous utilities."""
from functools import wraps
from typing import Any, Callable

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


def singlify(func: Callable):
    """Convert a single element list to just the element."""
    def wrapper(*args, **kwargs):
        output = func(*args, **kwargs)
        if type(output) in (list, tuple) and len(output) == 1:
            return output[0]
        elif type(output) is dict and len(output) == 1:
            key = list(output.keys())[0]
            return output[key]
        return output
    wraps(func, wrapper)
    return wrapper
