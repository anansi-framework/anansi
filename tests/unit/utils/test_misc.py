"""Test misc. utility functions."""
import pytest


A = {'a': 1}
B = {'a': 1}


@pytest.mark.parametrize('a,b,expected', (
    (1, 1, True),
    (1, 2, False),
    ('a', 'a', True),
    ('a', 'b', False),
    (A, A, True),
    (A, B, False),
))
def test_is_equal(a, b, expected):
    """Test equality comparison for two objects."""
    from anansi.utils import is_equal
    assert is_equal(a, b) is expected


@pytest.mark.parametrize('response,expected', (
    ('a', 'a'),
    (['a'], 'a'),
    (['a', 'b'], ['a', 'b']),
    (('a',), 'a'),
    (('a', 'b'), ('a', 'b')),
    ({'a': 1}, 1),
    ({'a': 1, 'b': 1}, {'a': 1, 'b': 1}),
))
def test_singlify(response, expected):
    """Test singlify decorator."""
    from anansi.utils import singlify

    @singlify
    def run():
        return response

    assert run() == expected
