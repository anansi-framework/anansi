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


def test_store_with_name():
    """Test store with naming context usage."""
    from anansi import Store, Model
    from anansi.exceptions import StoreNotFound

    class User(Model):
        __store__ = 'auth'

    class Book(Model):
        __store__ = 'content'

    auth = Store(name='auth')
    content = Store(name='content')

    u = User()
    b = Book()

    with pytest.raises(StoreNotFound):
        u.context.store
    with pytest.raises(StoreNotFound):
        b.context.store

    with auth, content:
        assert u.context.store is auth
        assert b.context.store is content
    with content:
        assert b.context.store is content
        with pytest.raises(StoreNotFound):
            u.context.store
    with auth:
        assert u.context.store is auth
        with pytest.raises(StoreNotFound):
            b.context.store

    with pytest.raises(StoreNotFound):
        u.context.store

    with pytest.raises(StoreNotFound):
        b.context.store


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
    from anansi import Store, Model, push_store, pop_store
    from anansi.exceptions import StoreNotFound

    class User(Model):
        __store__ = 'auth'

    class Book(Model):
        __store__ = 'content'

    auth = Store(name='auth')
    content = Store(name='content')

    push_store(auth)
    push_store(content)

    u = User()
    b = Book()

    assert u.context.store is auth
    assert b.context.store is content

    assert pop_store() is content
    assert pop_store() is auth
    assert pop_store() is None
    assert pop_store(auth) is None

    with pytest.raises(StoreNotFound):
        u.context.store
    with pytest.raises(StoreNotFound):
        b.context.store


def test_store_with_context_override():
    """Test setting store with a context override."""
    from anansi import Store, Model, push_store, pop_store

    class User(Model):
        __store__ = 'auth'

    auth = Store(name='auth')
    content = Store(name='content')

    push_store(auth)

    a = User()
    b = User(store=content)

    assert a.context.store is auth
    assert b.context.store is content

    a.context.store = content

    assert a.context.store is content
    assert b.context.store is content

    c = User()

    assert c.context.store is auth

    pop_store()


def test_store_backend_is_abstract():
    """Test to ensure that the backend class type is abstract."""
    from anansi.core.abstract_storage import AbstractStorage

    with pytest.raises(TypeError):
        AbstractStorage()
