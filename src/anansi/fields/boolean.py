"""Define Boolean field type."""
from anansi.core.field import Field

from typing import Any


class Boolean(Field):
    """Define basic string field data."""

    def __init__(self, data_type: Any=bool, **kw):
        super().__init__(data_type=data_type, **kw)
