"""Test anansi server utility methods."""
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
    from anansi.server.request_helpers import get_values_from_request

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
