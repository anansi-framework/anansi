"""Define store action types."""
from typing import Any


class MakeStorageValue:
    """StoreValue action."""

    def __init__(self, value: Any=None, context: 'Context'=None):
        self.context = context
        self.value = value
