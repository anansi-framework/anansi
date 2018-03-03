"""Test anansi server definition."""


def setup(*args):
    """Test setup method."""
    pass


def test_server_get_default_middleware():
    """Test default middleware for the server."""
    from anansi.server.server import get_default_middleware
    middleware = get_default_middleware()
    assert len(middleware) == 1


def test_server_make_app_config():
    """Test making an application for anansi."""
    from anansi.server import make_app

    app = make_app()
    assert app['anansi.config'] is not None

    app = make_app(config={'test': {'test2': True}})
    assert app['anansi.config']['test.test2'] is True


def test_server_make_app_with_addons(mocker):
    """Test creating a server with addon modules."""
    from anansi.server import make_app

    module = 'tests.unit.server.test_server'
    mock_setup = mocker.patch(module + '.setup')
    app = make_app(addons=[module])
    assert mock_setup.call_count == 1
    assert mock_setup.called_with(app)


def test_server_make_app_with_plugins(mocker):
    """Test creating a server with addon modules."""
    from anansi.server import make_app

    module = 'tests.unit.server.test_server'
    mock_setup = mocker.patch(module + '.setup')
    app = make_app(config={'server': {'plugins': [module]}})
    assert mock_setup.call_count == 1
    assert mock_setup.called_with(app)


def test_server_make_app_with_addons_and_plugins(mocker):
    """Test creating a server with addon modules."""
    from anansi.server import make_app

    module = 'tests.unit.server.test_server'
    mock_setup = mocker.patch(module + '.setup')
    app = make_app(
        addons=[module],
        config={'server': {'plugins': [module]}},
    )
    assert mock_setup.call_count == 2
    assert mock_setup.called_with(app)


def test_server_serve(mocker):
    """Test starting web service."""
    from anansi.server import serve

    mock_run_app = mocker.patch('anansi.server.server.web.run_app')
    mock_log_setup = mocker.patch('logging.config.dictConfig')

    log_config = {'level': 'DEBUG'}
    config = {
        'logging': log_config,
        'server': {
            'host': 'localhost',
            'port': 1234,
        }
    }
    serve(config=config)
    mock_log_setup.assert_called_with(log_config)
    assert mock_run_app.call_count == 1


def test_server_serve_with_root(mocker):
    """Test starting web service."""
    from anansi.server import serve

    mock_run_app = mocker.patch('anansi.server.server.web.run_app')
    mock_log_setup = mocker.patch('logging.config.dictConfig')

    log_config = {'level': 'DEBUG'}
    config = {
        'logging': log_config,
        'server': {
            'host': 'localhost',
            'port': 1234,
        }
    }
    serve(config=config, root='/api/v1')
    mock_log_setup.assert_called_with(log_config)
    assert mock_run_app.call_count == 1
