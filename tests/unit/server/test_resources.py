"""Test server resource methods."""
from aiohttp.test_utils import make_mocked_request
import json
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize('method,url', (
    ('GET', '/users'),
    ('POST', '/users'),
    ('PUT', '/users'),
    ('DELETE', '/users/1'),
    ('GET', '/users/1'),
    ('PATCH', '/users/1'),
    ('PUT', '/users/1'),
))
async def test_server_resources_add_resource(method, url):
    """Test resource server registration."""
    from anansi import Model
    from anansi.web.resources import add_resource
    from aiohttp.web import Application

    class User(Model):
        pass

    app = Application()
    add_resource(app, User)
    request = make_mocked_request(method, url)
    match_info = await app.router.resolve(request)
    assert match_info.http_exception is None


@pytest.mark.asyncio
@pytest.mark.parametrize('method,url', (
    ('DELETE', '/users/1'),
    ('GET', '/users/1'),
    ('PATCH', '/users/1'),
    ('PUT', '/users/1'),
))
async def test_server_resources_add_record_resource(method, url):
    """Test resource server registration."""
    from anansi import Model
    from anansi.web.resources import add_record_resource
    from aiohttp.web import Application

    class User(Model):
        pass

    app = Application()
    add_record_resource(app, User)
    request = make_mocked_request(method, url)
    match_info = await app.router.resolve(request)
    assert match_info.http_exception is None


@pytest.mark.asyncio
@pytest.mark.parametrize('method,url', (
    ('GET', '/users'),
    ('POST', '/users'),
    ('PUT', '/users'),
))
async def test_server_resources_add_model_resource(method, url):
    """Test resource server registration."""
    from anansi import Model
    from anansi.web.resources import add_model_resource
    from aiohttp.web import Application

    class User(Model):
        pass

    app = Application()
    add_model_resource(app, User)
    request = make_mocked_request(method, url)
    match_info = await app.router.resolve(request)
    assert match_info.http_exception is None


@pytest.mark.asyncio
async def test_create_record(mocker):
    """Test create record factory."""
    from anansi import Field, Model
    from anansi.web.resources import create_record

    async def get_json():
        return {
            'id': 1,
            'username': 'john.doe',
        }

    async def save():
        pass

    class User(Model):
        id = Field()
        username = Field()

    factory = create_record(User)
    request = make_mocked_request(
        'POST',
        '/users',
    )

    mocker.patch.object(User, 'save', side_effect=save)
    mocker.patch.object(request, 'json', side_effect=get_json)

    response = await factory(request)
    assert response.status == 200
    assert json.loads(response.body) == {
        'id': 1,
        'username': 'john.doe'
    }


@pytest.mark.asyncio
async def test_delete_record(mocker):
    """Test create record factory."""
    from anansi import Field, Model
    from anansi.web.resources import delete_record

    async def delete():
        pass

    async def fetch_record(request, model, match_key='', context=None):
        return model({'id': 1})

    class User(Model):
        id = Field()

    mocker.patch(
        'anansi.web.factories.fetch_record_from_request',
        side_effect=fetch_record,
    )
    mocker.patch.object(User, 'delete', side_effect=delete)

    handler = delete_record(User)
    request = make_mocked_request(
        'DELETE',
        '/users/1',
        match_info={'key': '1'},
    )
    response = await handler(request)
    assert response.status == 200
    assert json.loads(response.body) == {
        'status': 'ok',
    }


@pytest.mark.asyncio
async def test_get_record(mocker):
    """Test create record factory."""
    from anansi import Field, Model
    from anansi.web.resources import get_record

    async def fetch_record(request, model, match_key='', context=None):
        return model({'id': 1, 'username': 'john.doe'})

    class User(Model):
        id = Field()
        username = Field()

    mocker.patch(
        'anansi.web.factories.fetch_record_from_request',
        side_effect=fetch_record,
    )

    handler = get_record(User)
    request = make_mocked_request(
        'GET',
        '/users/1',
        match_info={'key': '1'},
    )
    response = await handler(request)
    assert response.status == 200
    assert json.loads(response.body) == {
        'id': 1,
        'username': 'john.doe',
    }


@pytest.mark.asyncio
async def test_get_records(mocker):
    """Test create record factory."""
    from anansi import Collection, Field, Model
    from anansi.web.resources import get_records

    class User(Model):
        id = Field()
        username = Field()

    async def select(context=None):
        a = User({'id': 1, 'username': 'john.doe'})
        b = User({'id': 2, 'username': 'jane.doe'})
        return Collection(records=[a, b])

    mocker.patch.object(User, 'select', side_effect=select)

    handler = get_records(User)
    request = make_mocked_request(
        'GET',
        '/users',
    )
    response = await handler(request)
    assert response.status == 200
    assert json.loads(response.body) == [{
        'id': 1,
        'username': 'john.doe',
    }, {
        'id': 2,
        'username': 'jane.doe',
    }]


@pytest.mark.asyncio
async def test_update_record(mocker):
    """Test create record factory."""
    from anansi import Field, Model
    from anansi.web.resources import update_record

    async def save():
        pass

    async def fetch_record(request, model, match_key='', context=None):
        return model({'id': 1, 'username': 'john.doe'})

    async def get_json():
        return {
            'username': 'jdoe',
        }

    class User(Model):
        id = Field()
        username = Field()

    handler = update_record(User)
    request = make_mocked_request(
        'PUT',
        '/users/1',
        match_info={'key': '1'},
    )

    mocker.patch.object(request, 'json', side_effect=get_json)
    mocker.patch.object(User, 'save', side_effect=save)
    mocker.patch(
        'anansi.web.factories.fetch_record_from_request',
        side_effect=fetch_record,
    )

    response = await handler(request)
    assert response.status == 200
    assert json.loads(response.body) == {
        'id': 1,
        'username': 'jdoe',
    }


@pytest.mark.asyncio
async def test_update_records(mocker):
    """Test create record factory."""
    from anansi import Collection, Field, Model
    from anansi.web.resources import update_records

    async def get_json():
        return {
            'active': True,
        }

    class User(Model):
        id = Field()
        username = Field()
        active = Field()

    async def select(context=None):
        a = User({
            'id': 1,
            'username': 'john.doe',
            'active': False})
        b = User({
            'id': 2,
            'username': 'jane.doe',
            'active': True
        })
        c = User({
            'id': 3,
            'username': 'john.smith',
            'active': False,
        })
        return Collection(records=[a, b, c])

    async def save():
        pass

    mocker.patch.object(User, 'select', side_effect=select)
    mocker.patch.object(User, 'save', side_effect=save)

    handler = update_records(User)
    request = make_mocked_request(
        'PUT',
        '/users',
        match_info={'key': '1'},
    )
    mocker.patch.object(request, 'json', side_effect=get_json)
    response = await handler(request)
    assert response.status == 200
    assert json.loads(response.body) == [{
        'id': 1,
        'username': 'john.doe',
        'active': True,
    }, {
        'id': 2,
        'username': 'jane.doe',
        'active': True,
    }, {
        'id': 3,
        'username': 'john.smith',
        'active': True,
    }]
