"""Define server functions."""
from aiohttp import web
from aiohttp.web_middlewares import normalize_path_middleware
from dotted.utils import dot
from typing import List
import aiohttp_cors
import importlib
import logging.config

DEFAULT_PORT = 8080

log = logging.getLogger(__name__)


def get_default_middleware() -> list:
    """Return default middleware for anansi server."""
    return [
        normalize_path_middleware(),
    ]


def make_app(
    *,
    addons: List[str]=None,
    config: dict=None,
    loop: 'asyncio.EventLoop'=None,
    middlewares: list=None,
) -> 'aiohttp.web.WebApplication':
    """Create WebApplication for anansi."""
    if middlewares is None:
        middlewares = get_default_middleware()

    config = dot(config or {})
    app = web.Application(
        loop=loop,
        middlewares=middlewares,
    )

    app['anansi.config'] = config

    cors_options = config.get('server.cors')
    if cors_options:
        defaults = {
            key: aiohttp_cors.ResourceOptions(**options)
            for key, options in cors_options.items()
        }
        aiohttp_cors.setup(app, defaults=defaults)

    plugins = config.get('server.plugins', [])
    if plugins:
        import_plugins(app, plugins)
    if addons:
        import_plugins(app, addons)

    return app


def import_plugins(
    app: 'aiohttp.web.WebApplication',
    plugins: list
):
    """Import and load server plugins."""
    for plugin in plugins:
        if plugin:
            module = importlib.import_module(plugin)
            module.setup(app)


def serve(
    *,
    addons: list=None,
    config: dict=None,
    host: str=None,
    loop: 'asyncio.EventLoop'=None,
    middlewares: list=None,
    port: int=None,
) -> int:
    """Run aiohttp server."""
    config = config or {}

    logging_config = config.pop('logging', {})
    if logging_config:
        logging.config.dictConfig(logging_config)
    else:
        logging.basicConfig()

    app = make_app(
        addons=addons,
        config=config,
        loop=loop,
        middlewares=middlewares,
    )

    host = host or config.get('server.host')
    port = port or config.get('server.port') or DEFAULT_PORT

    return web.run_app(app, host=host, port=port)
