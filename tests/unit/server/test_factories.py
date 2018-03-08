"""Test server factories."""
from aiohttp.test_utils import make_mocked_request
from aiohttp.web import HTTPForbidden
import json
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize('exception,status,expected', (
    (
        HTTPForbidden(),
        403,
        b'{"error": "HTTPForbidden", "description": "Forbidden"}'
    ),
    (
        RuntimeError(),
        500,
        b'{"error": "UnknownServerException", '
        b'"description": "Unknown server error."}',
    ),
))
async def test_error_response(exception, status, expected):
    """Test error response generation."""
    from anansi.server.factories import error_response
    response = error_response(exception)
    assert response.status == status
    assert response.body == expected


@pytest.mark.asyncio
async def test_model_route_factory(mocker):
    """Test creating a model route factory."""
    from anansi import Model, Field
    from anansi.server.factories import model_route_factory

    class User(Model):
        id = Field()

    @model_route_factory
    async def create_user(model, context):
        return {'id': 1}

    factory = create_user(User)
    request = make_mocked_request('GET', '/')
    response = await factory(request)
    assert response.status == 200
    assert json.loads(response.body) == {
        'id': 1,
    }


@pytest.mark.asyncio
async def test_model_route_factory_forbidden(mocker):
    """Test creating a model route factory."""
    from anansi import Model, Field
    from anansi.server.factories import model_route_factory

    async def permits(request, permit, context=None):
        return False

    mocker.patch(
        'anansi.server.factories.permits',
        side_effect=permits,
    )

    class User(Model):
        id = Field()

    @model_route_factory
    async def create_user(model, context):
        return {'id': 1}

    factory = create_user(User, permit='fail')
    request = make_mocked_request('GET', '/')
    response = await factory(request)
    assert response.status == 403
    assert json.loads(response.body) == {
        'description': 'Forbidden',
        'error': 'HTTPForbidden',
    }


@pytest.mark.asyncio
async def test_model_route_factory_error(mocker):
    """Test creating a model route factory."""
    from anansi import Model, Field
    from anansi.server.factories import model_route_factory

    async def permits(request, permit, context=None):
        return True

    mocker.patch(
        'anansi.server.factories.permits',
        side_effect=permits,
    )

    class User(Model):
        id = Field()

    @model_route_factory
    async def create_user(model, context):
        return {}['id']

    factory = create_user(User, permit='fail')
    request = make_mocked_request('GET', '/')
    response = await factory(request)
    assert response.status == 500
    assert json.loads(response.body) == {
        'description': 'Unknown server error.',
        'error': 'UnknownServerException',
    }


@pytest.mark.asyncio
async def test_record_route_factory(mocker):
    """Test creating a model route factory."""
    from anansi import Model, Field
    from anansi.server.factories import record_route_factory

    async def fetch_record(request, model, match_key='', context=None):
        return {'id': 1}

    mocker.patch(
        'anansi.server.factories.fetch_record_from_request',
        side_effect=fetch_record,
    )

    class User(Model):
        id = Field()

    @record_route_factory
    async def create_user(record, context):
        return record

    factory = create_user(User)
    request = make_mocked_request('GET', '/')
    response = await factory(request)
    assert response.status == 200
    assert json.loads(response.body) == {
        'id': 1,
    }


@pytest.mark.asyncio
async def test_record_route_factory_forbidden(mocker):
    """Test creating a model route factory."""
    from anansi import Model, Field
    from anansi.server.factories import record_route_factory

    async def permits(request, permit, context=None):
        return False

    mocker.patch(
        'anansi.server.factories.permits',
        side_effect=permits,
    )

    class User(Model):
        id = Field()

    @record_route_factory
    async def create_user(record, context):
        return {'id': 1}

    factory = create_user(User, permit='fail')
    request = make_mocked_request('GET', '/')
    response = await factory(request)
    assert response.status == 403
    assert json.loads(response.body) == {
        'description': 'Forbidden',
        'error': 'HTTPForbidden',
    }


@pytest.mark.asyncio
async def test_record_route_factory_error(mocker):
    """Test creating a model route factory."""
    from anansi import Model, Field
    from anansi.server.factories import record_route_factory

    async def permits(request, permit, context=None):
        return True

    mocker.patch(
        'anansi.server.factories.permits',
        side_effect=permits,
    )

    class User(Model):
        id = Field()

    @record_route_factory
    async def create_user(record, context):
        return {}['id']

    factory = create_user(User, permit='fail')
    request = make_mocked_request('GET', '/')
    response = await factory(request)
    assert response.status == 500
    assert json.loads(response.body) == {
        'description': 'Unknown server error.',
        'error': 'UnknownServerException',
    }
