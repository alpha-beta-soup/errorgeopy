try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Python geocoding in a disagreeing world',
    'author': 'Richard Law',
    'url': 'https://github.com/alpha-beta-soup/errorgeopy',
    'download_url': 'https://github.com/alpha-beta-soup/errorgeopy/archive/master.zip',
    'author_email': 'richard.m.law@gmail.com',
    'version': '0.1',
    'install_requires': ['nose','numpy','scipy','geopy'],
    'packages': ['errorgeopy'],
    'scripts': [],
    'name': 'errorgeopy'
}

setup(**config)
