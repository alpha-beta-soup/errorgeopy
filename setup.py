# python setup.py check
# python setup.py sdist
# python setup.py register sdist upload

from distutils.core import setup

# https://www.python.org/dev/peps/pep-0314/
# https://pypi.python.org/pypi?:action=list_classifiers
config = {
    'name': 'errorgeopy',
    'packages': ['errorgeopy'],
    'version': "0.0.2",
    'description': 'Python geocoding in a disagreeing world',
    'author': 'Richard Law',
    'author_email': 'richard.m.law@gmail.com',
    'url': 'https://github.com/alpha-beta-soup/errorgeopy',
    'download_url': 'https://github.com/alpha-beta-soup/errorgeopy/archive/master.zip',
    'requires': ['nose','numpy','scipy','geopy','shapely','pyhull','sklearn'],
    'scripts': [],
    'classifiers': [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: GIS"
    ],
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

Only supports Python 3.
"""

}

setup(**config)
