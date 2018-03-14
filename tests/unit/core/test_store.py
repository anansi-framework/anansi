"""Tests for the Store class."""
import pytest


def test_store_stack():
    """Test store stack creation."""
    from anansi import Store, current_store
    from anansi.exceptions import StoreNotFound

    store = Store()

    with pytest.raises(StoreNotFound):
        current_store()

    with store:
        assert current_store() is store

    with pytest.raises(StoreNotFound):
        current_store()


def test_store_stack_for_context():
    """Test store stack with context usage."""
    from anansi import Store, Model
    from anansi.exceptions import StoreNotFound

    store = Store()

    class User(Model):
        pass

    u = User()
    with pytest.raises(StoreNotFound):
        u.context.store

    with store:
        assert u.context.store is store

    with pytest.raises(StoreNotFound):
        u.context.store


def test_store_namespace():
    """Test store namespace context."""
    from anansi import Store, current_store
    from anansi.exceptions import StoreNotFound

    store = Store()
    with store:
        assert store.namespace == ''
        assert current_store().namespace == ''
        with store.for_namespace('auth') as auth_store:
            assert auth_store.namespace == 'auth'
            assert current_store().namespace == 'auth'
        assert store.namespace == ''
        assert current_store().namespace == ''

    with pytest.raises(StoreNotFound):
        assert current_store() is None


def test_store_with_global_reference():
    """Test store with global context registry."""
    from anansi import (
        Store,
        current_store,
        set_current_store,
    )
    from anansi.exceptions import StoreNotFound

    a = Store()
    b = Store()
    c = Store()

    with pytest.raises(StoreNotFound):
        assert current_store() is None

    set_current_store(a)
    with b:
        assert current_store() is b
        set_current_store(c)
        assert current_store() is c
    assert current_store() is a


def test_store_with_context_override():
    """Test setting store with a context override."""
    from anansi import Store, Model, set_current_store

    auth = Store()
    content = Store()

    class User(Model):
        __store__ = auth

    try:
        set_current_store(auth)

        a = User()
        b = User(store=content)

        assert a.context.store is auth
        assert b.context.store is content

        a.context.store = content

        assert a.context.store is content
        assert b.context.store is content

        c = User()

        assert c.context.store is auth
    finally:
        set_current_store(None)


def test_store_backend_is_abstract():
    """Test to ensure that the backend class type is abstract."""
    from anansi.core.abstract_storage import AbstractStorage

    with pytest.raises(TypeError):
        AbstractStorage()


@pytest.mark.asyncio
async def test_store_dispatch(mocker):
    """Test dispatching an action through store middleware."""
    from anansi import Store

    async def dispatch(action):
        return action

    store = Store()
    mock_dispatch = mocker.patch.object(
        store.middleware,
        'dispatch',
        side_effect=dispatch,
    )
    action = {}
    await store.dispatch(action)
    mock_dispatch.assert_called_with(action)
