# python setup.py check
# python setup.py sdist
# python setup.py register sdist upload

# from distutils.core import setup
import os
import sys
import codecs
import re
from setuptools import setup
from setuptools.command.test import test as TestCommand


def read(*parts):
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as fobj:
        return fobj.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        errcode = tox.cmdline(self.test_args)
        sys.exit(errcode)

# https://www.python.org/dev/peps/pep-0314/
# https://pypi.python.org/pypi?:action=list_classifiers
install_requires = [
    'Shapely >= 1.5', 'geopy >= 1', 'numpy >= 1', 'scikit-learn >= 0.15',
    'scipy >= 0.17', 'scikit-learn', 'fuzzywuzzy >= 0.11',
    'python-Levenshtein >= 0.12', 'pyproj>=1.9'
]

config = {
    'name': 'errorgeopy',
    'packages': ['errorgeopy'],
    'version': find_version("errorgeopy", "__init__.py"),
    'description': 'Python geocoding in a disagreeing world',
    'author': 'Richard Law',
    'author_email': 'richard.m.law@gmail.com',
    'url': 'https://github.com/alpha-beta-soup/errorgeopy',
    'download_url':
    'https://github.com/alpha-beta-soup/errorgeopy/archive/master.zip',
    'setup_requires': ['numpy'],
    'install_requires': install_requires,
    'scripts': [],
    'classifiers': [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment", "Intended Audience :: Developers",
        "Intended Audience :: Science/Research", "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: GIS"
    ],
    'tests_require': ['tox'],
    'cmdclass': {'test': Tox},
    'long_description': """\
Geocoding with automated indication of spatial error across providers
---------------------------------------------------------------------

Geocoding is the process of taking a string representing a real-world address,
and resolving that to a single point location. However different providers will
resolve the same addresses to different locations, and it can be important to
consider this spatial error. For example, when determining the census tract an
addresses should be linked to, there may be some error. This error can go
unacknowledged but still be very influential on analysis, similar to the famous
modifiable area-unit problem (MAUP), but for point representations of addresses.

This library can be used to determine spatial error across selected geocoding
providers. It can, for example, produce the convex hull of successful geocodes,
so you can imagine an address as a polygon. These individual points are also
available as a multipoint geometry.

Intended to work with as many of the providers supported by geopy as you care to
configure. Without configuration, will use free global provdiders that don't
require API tokens.

Only supports Python 3. Tested with Python 3.4 and 3.5.
"""
}

setup(**config)
