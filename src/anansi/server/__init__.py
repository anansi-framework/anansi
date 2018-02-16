"""Define aiohttp server interface for anansi REST API."""
from .resources import (  # noqa: F401
    add_resource,
)
from .server import (  # noqa: F401
    make_app,
    serve,
)
