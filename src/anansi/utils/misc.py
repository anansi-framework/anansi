"""Miscellaneous utilities."""
from functools import wraps
from typing import Any, Callable
import copy

BASIC_TYPES = {
    bool,
    bytes,
    float,
    int,
    str,
}


def dict_intersection(a: dict, b: dict) -> bool:
    """Return whether or not one dictionary intersects another."""
    for k, v in a:
        if b.get(k) != v:
            return False
    return True


def is_equal(a: Any, b: Any) -> bool:
    """Return whether or not a and b are equal by equality and identity."""
    if type(a) is type(b) and type(a) in BASIC_TYPES:
        return a == b
    return a is b


def deepmerge(source: dict, target: dict):
    """Merge two dictionaries together recursively."""
    output = copy.deepcopy(target)
    for key, value in source.items():
        if type(value) is dict:
            node = target.setdefault(key, {})
            output[key] = deepmerge(value, node)
        else:
            output[key] = value
    return output


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
