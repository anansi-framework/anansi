"""Tests for numerical fields."""


def test_float_field():
    """Test float field definition."""
    from anansi.fields import Float

    field = Float()
    assert field.data_type is float


def test_integer_field():
    """Test integer field definition."""
    from anansi.fields import Integer

    field = Integer()
    assert field.data_type is int


def test_serial_field():
    """Test serial field definition."""
    from anansi.fields import Serial

    default_flags = (
        Serial.Flags.Key |
        Serial.Flags.AutoAssign |
        Serial.Flags.Required
    )

    field = Serial()
    assert field.flags == default_flags

    field = Serial(flags={'Translatable'})
    assert field.flags == (default_flags | Serial.Flags.Translatable)

    field = Serial(flags=Serial.Flags.Translatable)
    assert field.flags == (default_flags | Serial.Flags.Translatable)
