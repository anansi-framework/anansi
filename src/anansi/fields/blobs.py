"""Data blob fields."""
from anansi.core.field import Field
from anansi.utils.json import dumps, loads
from typing import Any


class Object(Field):
    """Define JSON formatted text field."""

    def dump_value(self, value: Any, **context) -> Any:
        """Dump value to storage."""
        if type(value) is not str:
            return dumps(value)
        return value

    def load_value(self, value: Any, **context) -> Any:
        """Load value from storage."""
        if type(value) is str:
            return loads(value)
        return value
