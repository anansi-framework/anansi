"""Test JSON utility funtions."""
import datetime
import pytest


@pytest.mark.parametrize('obj,result', (
    (
        {'created': datetime.datetime(2000, 1, 1, 11, 59, 59)},
        '{"created": "2000-01-01T11:59:59"}',
    ),
    (
        {'created': datetime.date(2000, 1, 1)},
        '{"created": "2000-01-01"}',
    ),
    (
        {'created': datetime.time(11, 59, 59)},
        '{"created": "11:59:59"}'
    ),
))
def test_json_dumps(obj, result):
    """Test enhanced JSON dumps function."""
    from json import dumps as standard_dumps
    from anansi.utils.json import dumps as enhanced_dumps

    with pytest.raises(TypeError):
        standard_dumps(obj)

    assert enhanced_dumps(obj) == result


def test_json_dumps_passthrough():
    """Test dumping unknown object will pass through to the error."""
    from anansi.utils.json import dumps

    class TestClass:
        pass

    with pytest.raises(TypeError):
        assert dumps({'error': TestClass()}) is None
