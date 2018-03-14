"""Test command line utility."""
import pytest


def test_interface():
    """Test interface definition."""
    from anansi.cli import interface

    @interface(prog='test', version='1.2.3')
    def main():
        pass

    assert main.arg_parser is not None
    assert main.command is not None
    assert main.run is not None
    assert main.arg_parser.prog == 'test'


def test_command():
    """Test command definition."""
    from anansi.cli import interface

    @interface(prog='test')
    def main():
        pass

    @main.command()
    def test(name: str, enabled: bool=False):
        return name, enabled

    assert main.run(['test', 'bob']) == ('bob', False)
    assert main.run(['test', 'bob', '--enabled']) == ('bob', True)

    with pytest.raises(SystemExit):
        main.run(['test2'])


@pytest.mark.parametrize('args,values', (
    (
        ['serve'],
        {
            'addons': [],
            'config': None,
            'host': None,
            'port': None,
        },
    ),
    (
        [
            'serve',
            '--addons',
            'test.a,test.b',
            '--host',
            'localhost',
            '--port',
            '1234',
        ],
        {
            'addons': ['test.a', 'test.b'],
            'config': None,
            'host': 'localhost',
            'port': 1234,
        },
    ),
    (
        [
            'serve',
            '--config',
            './tests/unit/cli_config.json',
        ],
        {
            'addons': [],
            'config': {
                'server': {
                    'host': 'localhost',
                    'port': 1234,
                },
            },
            'host': None,
            'port': None,
        },
    ),
    (
        [
            'serve',
            '--config',
            './tests/unit/cli_config.yaml',
        ],
        {
            'addons': [],
            'config': {
                'server': {
                    'host': 'localhost',
                    'port': 1234,
                },
            },
            'host': None,
            'port': None,
        },
    ),
))
def test_serve(args, values, mocker):
    """Test serve command line interface."""
    from anansi.cli import cli

    mock_serve = mocker.patch('anansi.server.serve')
    cli.run(args)
    mock_serve.assert_called_with(**values)
