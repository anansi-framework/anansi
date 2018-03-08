"""Command line utility for anansi."""
import argparse
import inspect
import json
import sys
import yaml

from anansi import __version__


def make_command(parser: argparse.ArgumentParser) -> callable:
    """Define command decorator for a parser."""
    def outer(name='', **kw):
        def inner(func):
            subparsers = getattr(parser, 'subparsers', None)
            if not subparsers:
                subparsers = parser.add_subparsers(
                    description='valid subcommands',
                    help='additional help',
                    title='subcommands',
                )

            kw.setdefault('help', func.__doc__)
            sub_parser = subparsers.add_parser(name or func.__name__, **kw)
            sub_parser.set_defaults(func=func)

            spec = inspect.getfullargspec(func)
            num_kw = len(spec.defaults) if spec.defaults else 0
            for arg_name in spec.args[:-num_kw]:
                sub_parser.add_argument(
                    arg_name,
                    type=spec.annotations.get(arg_name, str),
                )

            if num_kw:
                for i, opt_name in enumerate(spec.args[-num_kw:]):
                    default = spec.defaults[i]
                    opt_type = spec.annotations.get(opt_name, str)
                    opt_kw = {}

                    if opt_type is bool:
                        action = 'store_{}'.format(not default).lower()
                        opt_kw['action'] = action
                    else:
                        opt_kw['type'] = opt_type

                    sub_parser.add_argument(
                        '--' + opt_name,
                        default=default,
                        **opt_kw,
                    )

            func.arg_parser = sub_parser
            func.command = make_command(sub_parser)
            return func
        return inner
    return outer


def make_runner(parser):
    """Create cli runner."""
    def runner(argv):
        arg_dict = vars(parser.parse_args(argv))
        func = arg_dict.pop('func', None)
        spec = inspect.getfullargspec(func)
        num_kw = len(spec.defaults) if spec.defaults else 0
        args = (
            arg_dict[arg_name]
            for arg_name in spec.args[:-num_kw]
            if arg_name in arg_dict
        )
        kw = {
            opt_name: arg_dict[opt_name]
            for opt_name in spec.args[-num_kw:]
            if opt_name in arg_dict
        }
        return func(*args, **kw)
    return runner


def interface(version=None, **kw):
    """Define root command line interface."""
    def wrapper(func):
        kw.setdefault('prog', func.__name__)
        kw.setdefault('description', func.__doc__)

        parser = argparse.ArgumentParser(**kw)
        parser.set_defaults(func=func)
        parser.add_argument(
            '--version',
            action='version',
            version=version or '0.0.0',
        )
        func.arg_parser = parser
        func.command = make_command(parser)
        func.run = make_runner(parser)
        return func
    return wrapper


@interface(prog='anansi', version=__version__)
def cli():  # noqa: D403
    """anansi command line interface."""
    pass


@cli.command()
def serve(
    addons: str='',
    config: str=None,
    host: str=None,
    port: int=None,
    root: str='',
):
    """Start webserver."""
    from anansi.server import serve

    if config:
        if config.endswith('.json'):
            with open(config, 'r') as f:
                conf = json.load(f)
        elif config.endswith('.yaml'):
            with open(config, 'r') as f:
                conf = yaml.load(f.read())
    else:
        conf = None

    return serve(
        addons=addons.split(',') if addons else [],
        config=conf,
        host=host,
        port=port,
        root=root,
    )


def main():  # pragma: no cover
    """Run main command line interface loop."""
    return cli.run(sys.argv[1:])


if __name__ == '__main__':  # pragma: no cover
    main()
