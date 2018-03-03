"""Define server functions."""
from aiohttp import web
from aiohttp.web_middlewares import normalize_path_middleware
from dotted.utils import dot
from typing import List
import importlib
import logging


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
    config = dot(config or {})
    app = web.Application(
        loop=loop,
        middlewares=middlewares,
    )
    app['anansi.config'] = config

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
    root: str=None,
) -> int:
    """Run aiohttp server."""
    config = dot(config or {})
    middlewares = middlewares or get_default_middleware()

    app = make_app(
        addons=addons,
        config=config,
        loop=loop,
        middlewares=middlewares,
    )

    logging_config = config.get('logging')
    if logging_config:
        logging.config.dictConfig(logging_config)

    host = host or config.get('server.host')
    port = port or config.get('server.port')
    root = root or config.get('server.root')

    if root:
        main_app = web.Application(loop=loop)
        main_app.add_subapp(root, app)
    else:
        main_app = app

    return web.run_app(main_app, host=host, port=port)
