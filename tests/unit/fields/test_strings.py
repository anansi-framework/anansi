"""Test String field classes."""
import pytest


@pytest.mark.parametrize('kwargs', (
    {},
    {'case_sensitive': False},
    {'max_length': 200},
    {'pattern': '\w+'},
))
def test_string_field(kwargs):
    """Test defining string field type."""
    from anansi.fields import String

    defaults = {
        'case_sensitive': True,
        'max_length': None,
        'pattern': '',
    }
    defaults.update(kwargs)

    field = String(**kwargs)

    assert field.data_type is str
    assert field.case_sensitive == defaults['case_sensitive']
    assert field.max_length == defaults['max_length']
    assert field.pattern == defaults['pattern']


@pytest.mark.asyncio
@pytest.mark.parametrize('kwargs,value,success', (
    ({}, None, True),
    ({}, '', True),
    ({'max_length': 10}, 't' * 8, True),
    ({'max_length': 10}, 't' * 10, True),
    ({'max_length': 10}, 't' * 11, False),
    ({'pattern': '\w+'}, 'test', True),
    ({'pattern': '^[a-f0-9]+$'}, 'af12', True),
    ({'pattern': '^[a-f0-9]+$'}, 'aero', False),
))
async def test_string_field_assertions(kwargs, value, success):
    """Test defining string field type."""
    from anansi.fields import String

    defaults = {
        'case_sensitive': True,
        'max_length': None,
        'pattern': '',
    }
    defaults.update(kwargs)

    field = String(**kwargs)
    if not success:
        with pytest.raises(AssertionError):
            await field.assert_valid(value)
    else:
        assert await field.assert_valid(value) is None


@pytest.mark.asyncio
@pytest.mark.parametrize('value,success', (
    (None, True),
    ('', True),
    ('(', False),
    ('^(\w+)@(\w+\.\w+)', True),
))
async def test_regex_field_assertions(value, success):
    """Test defining string field type."""
    from anansi.fields import Regex, String

    assert issubclass(Regex, String)

    field = Regex()
    if not success:
        with pytest.raises(AssertionError):
            await field.assert_valid(value)
    else:
        assert await field.assert_valid(value) is None


def test_text_field():
    """Test text field creation."""
    from anansi.fields import String, Text

    assert not issubclass(Text, String)

    field = Text()
    assert field.data_type == str
