"""Define Store class."""
from contextvars import ContextStack

from ..exceptions import StoreNotFound
from .middleware import Middleware

stack = ContextStack()
stack.current_store = None


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
        stack.__enter__()
        stack.current_store = self
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Pop this store off the top of the stack."""
        stack.__exit__()

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


def current_store() -> Store:
    """Return the current store based on context."""
    store = stack.current_store
    if store is None:
        raise StoreNotFound()
    return store


def set_current_store(store: Store):
    """Set the current store within the context."""
    stack.current_store = store
