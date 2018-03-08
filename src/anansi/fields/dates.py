"""Define datetime field types."""
import datetime
from typing import Any

from anansi.core.field import Field


class Date(Field):
    """Date field type."""

    def __init__(self, data_type: Any=datetime.date, **kw):
        super().__init__(data_type=data_type, **kw)


class Datetime(Field):
    """Datetime field type."""

    def __init__(
        self,
        *,
        as_utc: bool=False,
        data_type: Any=datetime.datetime,
        with_timezone: bool=False,
        **kw,
    ):
        super().__init__(data_type=data_type, **kw)

        self.as_utc = as_utc
        self.with_timezone = with_timezone


class Time(Field):
    """Time field type."""

    def __init__(self, data_type: Any=datetime.time, **kw):
        super().__init__(data_type=data_type, **kw)
