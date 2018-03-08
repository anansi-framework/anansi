"""Test decorator definition."""


def test_value_literal():
    """Test value literal decorator."""
    from anansi.core.decorators import value_literal

    value = {'type': 'test'}
    literal = value_literal(value)
    assert literal == value
    assert literal is not value
    assert literal.literal_value is value
