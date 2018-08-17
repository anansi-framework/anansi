"""Setup file for anansi."""
import glob
import os
import re
import subprocess
from typing import List, Tuple

from setuptools import Command, find_packages, setup
from setuptools.command.test import test as TestCommand


class mkdocs(Command):
    """Generate sphynx documentation."""

    description = 'generate documentation'
    user_options = []

    def initialize_options(self):
        """Initialize options."""
        pass

    def finalize_options(self):
        """Finalize options."""
        pass

    def run(self):
        """Generate documentation."""
        os.system('pip install -r requirements-dev.txt')
        os.system('sphinx-apidoc -f -o docs/source/api anansi')
        os.system('sphinx-build -b html docs/source docs/build')


class release(Command):
    """Tag and release new version of package to pypi."""

    description = 'runs the release command to generate a new distributable'
    user_options = [
        ('no-tests', None, 'Bypass the test validation before releasing')
    ]

    def initialize_options(self):
        """Initialize options."""
        self.no_tests = False

    def finalize_options(self):
        """Finalize options."""
        pass

    def run(self):
        """Run command."""
        if self.no_tests:
            print('[WARNING] No tests have been run for this release!')

        if not self.no_tests and os.system('python setup.py test'):
            print('[ERROR] Could not release, tests are failing!')
        else:
            os.system('python setup.py tag')
            os.system('python setup.py bdist_wheel bdist_egg upload')


class tag(Command):
    """Create new git tag for release."""

    description = 'tag the branch with the new version'
    user_options = [
        ('no-tag', None, 'Do not tag the repo before releasing'),
        ('no-push', None, 'Do not push tags')
    ]

    def initialize_options(self):
        """Initialize options."""
        self.no_tag = False
        self.no_push = False

    def finalize_options(self):
        """Finalize options."""
        pass

    def run(self):
        """Run command."""
        # generate the version information from the current git commit
        cmd = ['git', 'describe', '--match', 'v[0-9]*.[0-9]*.0']
        desc = subprocess.check_output(cmd).decode().strip()
        result = re.match(r'v([0-9]+)\.([0-9]+)\.0-([0-9]+)-(.*)', desc)

        major, minor, revision, hash_ = result.groups()

        # determine branch name
        cmd = ['git', 'branch']
        branch = subprocess.check_output(cmd).decode().strip()
        branch_type = re.search(r'\* ([a-z]*)', branch).group(1)
        release = '' if branch_type in ('release', 'master') else 'dev'

        version = '.'.join((major, minor, release + revision))
        print('generating version: {} from: {}'.format(version, desc))

        lines = (
            '# noqa',
            '__version__ = "{}"'.format(version),
            '__major__ = "{}"'.format(major),
            '__minor__ = "{}"'.format(minor),
            '__revision__ = "{}"'.format(release, revision),
            '__hash__ = "{}"'.format(hash_)
        )
        with open('./src/anansi/_version.py', 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')

        # tag this new release version
        if not self.no_tag:
            print('creating git tag:', 'v' + version)
            os.system('git tag -a v{0} -m "releasing {0}"'.format(version))
            if not self.no_push:
                os.system('git push --tags')
        else:
            print('warning: tagging ignored...')


class tox(TestCommand):
    """Run tox tests via python setup.py test."""

    def run_tests(self):
        """Run command."""
        import tox
        tox.cmdline()


def parse_requirements(path: str) -> Tuple[List[str], List[str]]:
    """Parse a requirements.txt file into a setuptools dependency tree."""
    last_url = None
    with open(path) as f:
        deps = []
        urls = []
        for line in f.readlines():
            if not line:
                continue
            elif '--' in line:
                match = re.match(r'--index-url\s+([\w\d:/.-]+)\s', line)
                if match:
                    last_url = match.group(1)
                    if not last_url.endswith('/'):
                        last_url += '/'
            else:
                if last_url:
                    urls.append(last_url + line.strip().lower())
                deps.append(line.strip())
        return deps, urls


def get_dependencies() -> Tuple[list, list, dict, list]:
    """Parse the requirements files into dependencies."""
    install_requires = []
    extras_require = {}
    tests_require = []
    links = []

    if os.path.isfile('requirements.txt'):
        reqs, urls = parse_requirements('requirements.txt')
        install_requires.extend(filter(bool, reqs))
        links.extend(filter(bool, urls))

    if os.path.isfile('tests/requirements.txt'):
        reqs, urls = parse_requirements('tests/requirements.txt')
        tests_require.extend(filter(bool, reqs))
        links.extend(filter(bool, urls))

    for fname in glob.glob('requirements-*.txt'):
        extra_name = fname.split('-', 1)[1].split('.')[0]
        reqs, urls = parse_requirements(fname)
        extras_require[extra_name] = filter(bool, reqs)
        links.extend(filter(bool, urls))

    return install_requires, tests_require, extras_require, links


def get_version() -> str:
    """Parse the version triplet for this release."""
    try:
        with open('./src/anansi/_version.py', 'r') as f:
            content = f.read()
        return re.search('__version__ = "(.*)"', content).group(1).strip('_')
    except Exception:
        return '0.0.dev0'


if __name__ == '__main__':
    install_requires, tests_require, extras_require, links = get_dependencies()
    version = get_version()
    packages = find_packages('src')

    setup(
        author='Eric Hulser',
        author_email='eric.hulser@gmail.com',
        description='Asyncio data modeling library',
        cmdclass={
            'tag': tag,
            'release': release,
            'mkdocs': mkdocs,
            'test': tox
        },
        entry_points={
            'console_scripts': [
                'anansi=anansi.cli:main',
            ],
        },
        extras_require=extras_require,
        install_requires=install_requires,
        license='MIT',
        maintainer='eric.hulser@gmail.com',
        maintainer_email='eric.hulser@gmail.com',
        name='anansi',
        packages=packages,
        package_dir={'': 'src'},
        tests_require=tests_require,
        test_suite='tests',
        url='https://github.com/anansi-framework/anansi',
        version=version,
    )
