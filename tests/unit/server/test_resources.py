"""Test server resource methods."""
from aiohttp.test_utils import make_mocked_request
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
    from anansi.server.resources import add_resource
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
    from anansi.server.resources import add_record_resource
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
    from anansi.server.resources import add_model_resource
    from aiohttp.web import Application

    class User(Model):
        pass

    app = Application()
    add_model_resource(app, User)
    request = make_mocked_request(method, url)
    match_info = await app.router.resolve(request)
    assert match_info.http_exception is None
