"""Test anansi server utility methods."""
from aiohttp.web import HTTPNotFound
from aiohttp.test_utils import make_mocked_request
import pytest
import json


@pytest.mark.asyncio
@pytest.mark.parametrize('params,payload,expected', (
    ({'number': '1'}, '', {'number': 1}),
    ({}, '{"number": 1}', {'number': 1}),
    (
        {'is_active': 'false'},
        '{"name": "Test"}',
        {'is_active': False, 'name': 'Test'}
    ),
))
async def test_get_values_from_request(params, payload, expected, mocker):
    """Return values from a request based on schema."""
    from anansi import Model
    from anansi.fields import Boolean, Integer, Serial, String
    from anansi.web.request_helpers import get_values_from_request

    request = make_mocked_request('GET', '/')

    async def get_post():
        return params

    async def get_json():
        return json.loads(payload)

    class TestModel(Model):
        id = Serial()
        number = Integer()
        is_active = Boolean()
        name = String()

    mocker.patch.object(request, 'json', side_effect=get_json)
    mocker.patch.object(request, 'post', side_effect=get_post)

    values = await get_values_from_request(request, TestModel)
    assert values == expected


@pytest.mark.asyncio
@pytest.mark.parametrize('key,exception', (
    (0, HTTPNotFound()),
    (1, None),
    ('jdoe', None),
))
async def test_fetch_record_from_request(key, exception, mocker):
    """Test fetching a record from a keypath."""
    from anansi import Model, Field
    from anansi.web.request_helpers import fetch_record_from_request

    request = make_mocked_request('GET', '/', match_info={'key': str(key)})

    class User(Model):
        id = Field(flags={'Key'})

    async def fetch(key, context=None):
        if not key:
            return None
        return {'id': key}

    mock_fetch = mocker.patch.object(User, 'fetch', side_effect=fetch)
    if exception is not None:
        with pytest.raises(type(exception)):
            await fetch_record_from_request(request, User)
        mock_fetch.assert_called_once()
    else:
        record = await fetch_record_from_request(request, User)
        assert record == {'id': key}
        mock_fetch.assert_called_once()


def test_load_param():
    """Test parsing url params."""
    from anansi.web.request_helpers import load_param

    assert load_param('') == ''
    assert load_param('1') == 1
    assert load_param('test') == 'test'
    assert load_param('{"test": true}') == {'test': True}


@pytest.mark.asyncio
@pytest.mark.parametrize('method', ('GET', 'PUT', 'PATCH', 'POST', 'DELETE'))
@pytest.mark.parametrize('path,context', (
    ('/?page=1', {'page': 1}),
    ('/?distinct=field_a,field_b', {'distinct': {'field_a', 'field_b'}}),
    ('/?distinct=true', {'distinct': True}),
    ('/?start=1&limit=10', {'start': 1, 'limit': 10}),
    ('/?page=5&page_size=100', {'page': 5, 'page_size': 100}),
    ('/?a=1&b=2', {'where': {
        'type': 'group',
        'op': 'and',
        'queries': [{
            'type': 'query',
            'model': None,
            'op': 'is',
            'left': 'a',
            'right': 1,
        }, {
            'type': 'query',
            'model': None,
            'op': 'is',
            'left': 'b',
            'right': 2,
        }]
    }}),
))
async def test_make_context_from_request(method, path, context):
    """Test generating context from request params."""
    from anansi.web.request_helpers import make_context_from_request
    request = make_mocked_request(method, path)
    actual = await make_context_from_request(request)
    actual_dict = actual.dump()
    context['scope'] = {'request': request}
    for key, value in context.items():
        assert actual_dict[key] == value
