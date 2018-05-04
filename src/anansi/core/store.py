"""Define Store class."""
from contextvars import ContextVar

from ..exceptions import StoreNotFound
from .middleware import Middleware
from ..middleware.storage import storage_middleware


_current_store = ContextVar('current_store')


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
        middleware = middleware or Middleware([storage_middleware])

        self._middleware = middleware
        self._storage = None
        self.middleware = middleware
        self.name = name
        self.namespace = namespace
        self._context_token = None

        if storage:
            self.set_storage(storage)

    def __enter__(self):
        """Push this store onto the top of the stack."""
        self._context_token = _current_store.set(self)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Pop this store off the top of the stack."""
        _current_store.reset(self._context_token)

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

    def get_storage(self) -> 'AbstractStorage':
        """Return storage backend for this store."""
        return self._storage

    def set_storage(self, storage: 'AbstractStorage'):
        """Set storage instance for this store."""
        self._storage = storage

        middleware = Middleware()
        middleware.add(self._middleware)
        try:
            middleware.add(getattr(storage, 'middleware'))
        except AttributeError:
            pass
        self.middleware = middleware

    storage = property(get_storage, set_storage)


def current_store() -> Store:
    """Return the current store based on context."""
    try:
        store = _current_store.get()
    except LookupError:
        raise StoreNotFound()
    else:
        return store


def set_current_store(store: Store):
    """Set the current store within the context."""
    _current_store.set(store)
