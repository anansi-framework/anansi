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


@pytest.mark.asyncio
async def test_store_delete_collection(mocker):
    """Test deleting a collection from a store."""
    from anansi import Store
    from anansi.actions import DeleteCollection

    async def dispatch(action):
        return action

    store = Store()
    mocker.patch.object(store.middleware, 'dispatch', side_effect=dispatch)

    records = []
    context = {}
    action = await store.delete_collection(records, context)
    assert type(action) is DeleteCollection
    assert action.collection is records
    assert action.context is context


@pytest.mark.asyncio
async def test_store_delete_record(mocker):
    """Test deleting a record from a store."""
    from anansi import Store
    from anansi.actions import DeleteRecord

    async def dispatch(action):
        return action

    store = Store()
    mocker.patch.object(store.middleware, 'dispatch', side_effect=dispatch)

    record = {}
    context = {}
    action = await store.delete_record(record, context)
    assert type(action) is DeleteRecord
    assert action.record is record
    assert action.context is context


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


@pytest.mark.asyncio
async def test_store_get_count(mocker):
    """Test deleting a record from a store."""
    from anansi import Store
    from anansi.actions import GetCount

    async def dispatch(action):
        return action

    store = Store()
    mocker.patch.object(store.middleware, 'dispatch', side_effect=dispatch)

    model = {}
    context = {}
    action = await store.get_count(model, context)
    assert type(action) is GetCount
    assert action.model is model
    assert action.context is context


@pytest.mark.asyncio
async def test_store_get_records(mocker):
    """Test deleting a record from a store."""
    from anansi import Store
    from anansi.actions import GetRecords

    async def dispatch(action):
        return action

    store = Store()
    mocker.patch.object(store.middleware, 'dispatch', side_effect=dispatch)

    model = {}
    context = {}
    action = await store.get_records(model, context)
    assert type(action) is GetRecords
    assert action.model is model
    assert action.context is context


@pytest.mark.asyncio
async def test_store_save_record(mocker):
    """Test deleting a record from a store."""
    from anansi import Store
    from anansi.actions import SaveRecord

    async def dispatch(action):
        return action

    store = Store()
    mocker.patch.object(store.middleware, 'dispatch', side_effect=dispatch)

    record = {}
    context = {}
    action = await store.save_record(record, context)
    assert type(action) is SaveRecord
    assert action.record is record
    assert action.context is context


@pytest.mark.asyncio
async def test_store_save_collection(mocker):
    """Test deleting a collection from a store."""
    from anansi import Store
    from anansi.actions import SaveCollection

    async def dispatch(action):
        return action

    store = Store()
    mocker.patch.object(store.middleware, 'dispatch', side_effect=dispatch)

    records = []
    context = {}
    action = await store.save_collection(records, context)
    assert type(action) is SaveCollection
    assert action.collection is records
    assert action.context is context
