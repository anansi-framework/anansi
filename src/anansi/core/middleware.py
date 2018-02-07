"""Define Middleware class type."""


async def _default_handler(action):
    return action


class Middleware:
    """Middleware type."""

    def __init__(self, middleware: list=None):
        self._middleware = middleware or []

    def add(self, *middleware):
        """Add new middleware methods to the list."""
        for item in middleware:
            if isinstance(item, Middleware):
                self._middleware.extend(item._middleware)
            else:
                self._middleware.append(item)

    async def dispatch(self, action: 'Action'):
        """Dispatch an action through the middleware."""
        handler = _default_handler
        for middleware in reversed(self._middleware):
            handler = await middleware(handler)
        return await handler(action)

    def insert(self, index, *middleware):
        """Insert new middleware methods to the list at the given index."""
        insert_items = []
        for item in middleware:
            if isinstance(item, Middleware):
                insert_items.extend(item._middleware)
            else:
                insert_items.append(item)

        self._middleware = (
            self._middleware[:index] +
            insert_items +
            self._middleware[index:]
        )
