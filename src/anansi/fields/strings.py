"""Define String field types."""
from typing import Any
import logging
import re

from anansi.core.field import Field

log = logging.getLogger(__name__)


class String(Field):
    """Define basic string field data."""

    def __init__(
        self,
        *,
        case_sensitive: bool=True,
        data_type: Any=str,
        max_length: int=None,
        pattern: str='',
        **kw
    ):
        super().__init__(data_type=data_type, **kw)

        self.case_sensitive = case_sensitive
        self.max_length = max_length
        self.pattern = pattern

    async def assert_valid(self, value: Any):
        """Assert that the given value is valid for this field."""
        await super().assert_valid(value)

        if value is None:
            return
        if self.pattern:
            matched = re.match(self.pattern, value) is not None
            assert matched, 'Value does not match pattern.'
        if self.max_length:
            assert len(value) <= self.max_length, 'Value exceeds max length.'


class Regex(String):
    """Regex data field."""

    async def assert_valid(self, value: Any):
        """Assert a valid regular expression is supplied."""
        await super().assert_valid(value)

        if value is None:
            return
        else:
            try:
                re.compile(value)
            except re.error:
                log.exception('Failed to compile regex.')
                raise AssertionError('Invalid regular expression.')


class Text(Field):
    """Define basic string field data."""

    def __init__(self, data_type: Any=str, **kw):
        super().__init__(data_type=data_type, **kw)
