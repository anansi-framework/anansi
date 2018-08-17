"""Test basic inclusion of the package."""
import importlib

PACKAGE = 'anansi'


def test_package_import():
    """Ensure top-level package imports."""
    assert importlib.import_module(PACKAGE) is not None


def test_package_version():
    """Ensure package version has proper format."""
    import re
    module = importlib.import_module(PACKAGE)

    assert re.match(r'^\d+\.\d+\.(dev)?\d+$', module.__version__) is not None


def test_all_modules_import():
    """Ensure all sub-modules can be imported."""
    import pkgutil
    import traceback

    failures = {}

    def walk_packages(package):
        for (
            importer,
            module,
            is_pkg
        ) in pkgutil.walk_packages(package.__path__):
            package_name = '{0}.{1}'.format(package.__name__, module)

            try:
                sub_module = importlib.import_module(package_name)
            except ImportError:
                failures[package_name] = traceback.format_exc()
            else:
                if is_pkg:
                    walk_packages(sub_module) is True

    root_module = importlib.import_module(PACKAGE)
    walk_packages(root_module)

    # log any failed imports
    for module, stack in failures.items():
        print('----------------')
        print('[IMPORT ERROR] {0}'.format(module))
        print(stack)

    assert failures == {}
