"""Define Store class."""

from typing import List, Type

from ..exceptions import StoreNotFound
from ..actions import (
    DeleteCollection,
    DeleteRecord,
    GetCount,
    GetRecords,
    SaveCollection,
    SaveRecord,
)
from .middleware import Middleware

STORE_STACK = []


class Store:
    """Define storage for models."""

    def __init__(
        self,
        *,
        storage: 'AbstractStorage'=None,
        middleware: 'Middleware'=None,
        name: str='',
        namespace: str=''
    ):
        middleware = middleware or Middleware()
        if storage:
            try:
                middleware.add(getattr(storage, 'middleware'))
            except AttributeError:
                pass

            from ..middleware.storage import storage_middleware
            middleware.add(storage_middleware(storage))
        self.middleware = middleware
        self.name = name
        self.namespace = namespace
        self.storage = storage

    def __enter__(self):
        """Push this store onto the top of the stack."""
        push_store(self)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Pop this store off the top of the stack."""
        pop_store(self)

    async def delete_collection(
        self,
        collection: 'Collection',
        context: 'Context'
    ) -> int:
        """Dispatch the DeleteCollection action."""
        action = DeleteCollection(collection=collection, context=context)
        return await self.middleware.dispatch(action)

    async def delete_record(self, record: 'Model', context: 'Context') -> int:
        """Dispatch the DeleteRecord action."""
        action = DeleteRecord(record=record, context=context)
        return await self.middleware.dispatch(action)

    async def dispatch(self, action):
        """Dispatch action through the store middleware."""
        return await self.middleware.dispatch(action)

    def for_namespace(self, namespace: 'str') -> 'Store':
        """Return a copy of this storage with a given namespace."""
        return Store(
            middleware=self.middleware,
            name=self.name,
            namespace=namespace,
        )

    async def get_count(self, model: Type['Model'], context: 'Context') -> int:
        """Dispatch GetCount action."""
        action = GetCount(model=model, context=context)
        return await self.middleware.dispatch(action)

    async def get_records(
        self,
        model: Type['Model'],
        context: 'Context'
    ) -> List[dict]:
        """Dispatch GetRecords action."""
        action = GetRecords(model=model, context=context)
        return await self.middleware.dispatch(action)

    async def save_record(self, record: 'Model', context: 'Context') -> dict:
        """Dispatch SaveRecord action."""
        action = SaveRecord(
            record=record,
            context=context,
        )
        return await self.middleware.dispatch(action)

    async def save_collection(
        self,
        collection: 'Collection',
        context: 'Context'
    ) -> list:
        """Dispatch SaveCollection action."""
        action = SaveCollection(collection=collection, context=context)
        return await self.middleware.dispatch(action)


def current_store(name: str=None) -> Store:
    """Return the current active store."""
    if not name:
        try:
            return STORE_STACK[-1]
        except IndexError:
            raise StoreNotFound()

    for store in STORE_STACK:
        if store.name == name:
            return store
    else:
        raise StoreNotFound()


def push_store(store: Store) -> Store:
    """Push the store instance to the top of the stack."""
    STORE_STACK.append(store)
    return store


def pop_store(store: Store=None) -> Store:
    """Pop the store instance from the end of the stack."""
    if store is not None:
        try:
            STORE_STACK.remove(store)
        except ValueError:
            pass
        else:
            return store
        return None

    try:
        return STORE_STACK.pop()
    except IndexError:
        pass
    return None
