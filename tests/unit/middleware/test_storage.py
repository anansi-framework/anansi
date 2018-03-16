"""Test storage middleware."""
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_storage():
    """Define a mocked storage class."""
    from anansi import AbstractStorage

    class MockStorage(AbstractStorage):
        async def delete_record(self, record, context):
            raise NotImplementedError

        async def delete_collection(self, collection, context):
            raise NotImplementedError

        async def get_count(self, model, context):
            raise NotImplementedError

        async def get_records(self, model, context):
            raise NotImplementedError

        async def save_record(self, record, context):
            raise NotImplementedError

        async def save_collection(self, record, context):
            raise NotImplementedError

    return MockStorage()


@pytest.mark.asyncio
async def test_storage_middleware_delete_record(mock_storage, mocker):
    """Test deleting record from storage middleware."""
    from anansi import Store, make_context
    from anansi.actions import DeleteRecord
    from anansi.middleware.storage import storage_middleware

    async def delete_record(record, context):
        return {'status': 'ok'}

    async def next_action(action):
        return action

    mock_delete_record = mocker.patch.object(
        mock_storage,
        'delete_record',
        side_effect=delete_record,
    )
    mock_next_action = MagicMock(side_effect=next_action)

    record = {'id': 1}
    context = make_context(
        namespace='public',
        store=Store(storage=mock_storage),
    )

    handler = await storage_middleware(mock_next_action)
    result = await handler(DeleteRecord(record, context))
    mock_delete_record.assert_called_with(record, context)
    mock_next_action.assert_not_called()
    assert result == {'status': 'ok'}


@pytest.mark.asyncio
async def test_storage_middleware_delete_collection(mock_storage, mocker):
    """Test deleting record from storage middleware."""
    from anansi import Store, make_context
    from anansi.actions import DeleteCollection
    from anansi.middleware.storage import storage_middleware

    async def delete_collection(collection, context):
        return {'status': 'ok'}

    async def next_action(action):
        return action

    mock_delete_collection = mocker.patch.object(
        mock_storage,
        'delete_collection',
        side_effect=delete_collection,
    )
    mock_next_action = MagicMock(side_effect=next_action)

    collection = [{'id': 1}]
    context = make_context(
        namespace='public',
        store=Store(storage=mock_storage),
    )

    handler = await storage_middleware(mock_next_action)
    result = await handler(DeleteCollection(collection, context))
    mock_delete_collection.assert_called_with(collection, context)
    mock_next_action.assert_not_called()
    assert result == {'status': 'ok'}


@pytest.mark.asyncio
async def test_storage_middleware_get_count(mock_storage, mocker):
    """Test deleting record from storage middleware."""
    from anansi import Store, make_context
    from anansi.actions import FetchCount
    from anansi.middleware.storage import storage_middleware

    async def get_count(model, context):
        return {'status': 'ok'}

    async def next_action(action):
        return action

    mock_get_count = mocker.patch.object(
        mock_storage,
        'get_count',
        side_effect=get_count,
    )
    mock_next_action = MagicMock(side_effect=next_action)

    model = {'id': 1}
    context = make_context(
        namespace='public',
        store=Store(storage=mock_storage),
    )

    handler = await storage_middleware(mock_next_action)
    result = await handler(FetchCount(model, context))
    mock_get_count.assert_called_with(model, context)
    mock_next_action.assert_not_called()
    assert result == {'status': 'ok'}


@pytest.mark.asyncio
async def test_storage_middleware_get_records(mock_storage, mocker):
    """Test deleting record from storage middleware."""
    from anansi import Store, make_context
    from anansi.actions import FetchCollection
    from anansi.middleware.storage import storage_middleware

    async def get_records(model, context):
        return {'status': 'ok'}

    async def next_action(action):
        return action

    mock_get_records = mocker.patch.object(
        mock_storage,
        'get_records',
        side_effect=get_records,
    )
    mock_next_action = MagicMock(side_effect=next_action)

    model = {'id': 1}
    context = make_context(
        namespace='public',
        store=Store(storage=mock_storage),
    )

    handler = await storage_middleware(mock_next_action)
    result = await handler(FetchCollection(model, context))
    mock_get_records.assert_called_with(model, context)
    mock_next_action.assert_not_called()
    assert result == {'status': 'ok'}


@pytest.mark.asyncio
async def test_storage_middleware_make_store_value(mock_storage, mocker):
    """Test deleting record from storage middleware."""
    from anansi.actions import MakeStorageValue
    from anansi.middleware.storage import storage_middleware

    async def next_action(action):
        return action

    mock_next_action = MagicMock(side_effect=next_action)

    value = {'id': 1}

    handler = await storage_middleware(mock_next_action)
    result = await handler(MakeStorageValue(value))
    mock_next_action.assert_not_called()
    assert result == value


@pytest.mark.asyncio
async def test_storage_middleware_save_record(mock_storage, mocker):
    """Test deleting record from storage middleware."""
    from anansi import Store, make_context
    from anansi.actions import SaveRecord
    from anansi.middleware.storage import storage_middleware

    async def save_record(record, context):
        return {'status': 'ok'}

    async def next_action(action):
        return action

    mock_save_record = mocker.patch.object(
        mock_storage,
        'save_record',
        side_effect=save_record,
    )
    mock_next_action = MagicMock(side_effect=next_action)

    record = {'id': 1}
    context = make_context(
        namespace='public',
        store=Store(storage=mock_storage),
    )

    handler = await storage_middleware(mock_next_action)
    result = await handler(SaveRecord(record, context))
    mock_save_record.assert_called_with(record, context)
    mock_next_action.assert_not_called()
    assert result == {'status': 'ok'}


@pytest.mark.asyncio
async def test_storage_middleware_save_collection(mock_storage, mocker):
    """Test deleting record from storage middleware."""
    from anansi import Store, make_context
    from anansi.actions import SaveCollection
    from anansi.middleware.storage import storage_middleware

    async def save_collection(collection, context):
        return {'status': 'ok'}

    async def next_action(action):
        return action

    mock_save_collection = mocker.patch.object(
        mock_storage,
        'save_collection',
        side_effect=save_collection,
    )
    mock_next_action = MagicMock(side_effect=next_action)

    collection = [{'id': 1}]
    context = make_context(
        namespace='public',
        store=Store(storage=mock_storage),
    )

    handler = await storage_middleware(mock_next_action)
    result = await handler(SaveCollection(collection, context))
    mock_save_collection.assert_called_with(collection, context)
    mock_next_action.assert_not_called()
    assert result == {'status': 'ok'}


@pytest.mark.asyncio
async def test_storage_middleware_passthrough(mock_storage, mocker):
    """Test deleting record from storage middleware."""
    from anansi.middleware.storage import storage_middleware

    async def next_action(action):
        return action

    mock_next_action = MagicMock(side_effect=next_action)

    action = {'type': 'test'}

    handler = await storage_middleware(mock_next_action)
    result = await handler(action)
    mock_next_action.assert_called_with(action)
    assert result == action
