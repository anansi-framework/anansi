"""Define numerical field types."""
from anansi.core.field import Field

from typing import Any


class Float(Field):
    """Define field type with float data."""

    def __init__(self, data_type: Any=float, **kw):
        super().__init__(data_type=data_type, **kw)


class Integer(Field):
    """Define basic string field data."""

    def __init__(self, data_type: Any=int, **kw):
        super().__init__(data_type=data_type, **kw)
