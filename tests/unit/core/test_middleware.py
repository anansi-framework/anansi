"""Tests for the middleware class."""
import pytest


@pytest.mark.asyncio
async def test_middleware():
    """Test middleware creation."""
    from anansi import Middleware

    middleware = Middleware()
    action = {'type': 'test'}
    result = await middleware.dispatch(action)
    assert result is action


@pytest.mark.asyncio
async def test_middlware_handlers():
    """Test middleware creation with handlers."""
    from anansi import Middleware

    def factory(name):
        async def middleware(next):
            async def handler(action):
                action['path'].append(name)
                return await next(action)
            return handler
        return middleware

    middleware = Middleware()
    middleware.add(factory('a'))
    middleware.add(factory('b'))
    middleware.add(factory('c'))
    middleware.insert(0, factory('z'))

    action = {'path': []}
    await middleware.dispatch(action)
    assert action['path'] == ['z', 'a', 'b', 'c']


@pytest.mark.asyncio
async def test_middleware_extension():
    """Test middleware extension with handlers."""
    from anansi import Middleware

    def factory(name):
        async def middleware(next):
            async def handler(action):
                action['path'].append(name)
                return await next(action)
            return handler
        return middleware

    a = Middleware([factory('a'), factory('b')])
    b = Middleware([factory('c'), factory('d')])

    middleware = Middleware()
    middleware.add(a)
    middleware.insert(0, b)

    action = {'path': []}
    await middleware.dispatch(action)
    assert action['path'] == ['c', 'd', 'a', 'b']
