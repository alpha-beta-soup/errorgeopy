errorgeopy
==========

Python geocoding in a disagreeing world

.. raw:: html

   <!-- pandoc --from=markdown --to=rst --output=README.rst README.md -->

|Dependencies| |PyPI version| |Build status|

Wraps `geopy <https://github.com/geopy/geopy>`__ geocoding to expose a
simple way to use multiple providers of geocoding services
simultaneously (with ``multiprocessing``), and provide a report of the
ensuing spatial uncertainty in the final location.

0. Configure your desired/allowed geocoding providers (``config.yml``).
1. Geocode an address using the errorgeopy ``geocode`` wrapper.
2. Recieve a multipoint of the geocoded address locations, the `convex
   hull <http://scipy.github.io/devdocs/generated/scipy.spatial.ConvexHull.html>`__
   of the result locations, the `concave
   hull <http://blog.thehumangeo.com/2014/05/12/drawing-boundaries-in-python/>`__
   of the results, various types of centroid, and quantitative measures
   of spatial agreement across component providers---as well as
   maintaining access to the original results.

Installation
============

Requires Python 3; only tested with Python 3.4

``pip install errorgeopy``

Dependencies
------------

-  ``geopy``
-  ``shapely`` (outputs generally are ``shapely.geometry`` types in
   geographic coordinates)
-  ``sklearn``
-  ``scipy``

Why?
====

Geocoding is very hard, although consumer-grade APIs make the process
seem very easy. Intuitively, it does seem easy: address goes in, point
comes out. `That's what Osaka Seafood Concern is all about. Every
truckload of addresses you geocode brings you 31 cents closer to those
tickets home! <https://www.youtube.com/watch?v=cIosb69x9iI>`__

But what if two different geocoding services both claim a successful
address-level match, but the output location is different? If it is a
subtle difference, it probably doesn't matter, especially if both
addresses are within the same parcel. If it is a significant difference,
it is possible that the two services have identified an ambiguity in the
input address, or that one of them is just wrong, or that one of them
can only match down to the suburb, and not the street or numberered
address. Using more services may help you identify such a situtation and
ignore such "minority opinions". **This is exactly what errorgeopy can
do for you.**

For example, given a configuration (not shown) for making requests to
multiple geocoding services, errorgeopy can return identified clusters
of addresses, in order, with the first cluster being the largest (and
therefore most likely positive match):

.. code:: python

    >>> import os, yaml
    >>> from errorgeopy.geocoders import GeocoderPool
    >>> # Get geocoder configuration from a file
    >>> config = './configuration.yml'
    >>> g_pool = GeocoderPool.fromfile(config, yaml.load)
    >>> test = '66 Great North Road, Grey Lynn, Auckland, New Zealand'
    >>> location = g_pool.geocode(test)
    >>> print(location.clusters)
    {
      0: {
        'centre': 'POINT (174.7445831298828 -36.8640251159668)',
        'members': [
          (174.7375733, -36.8654),
          (174.74137, -36.86642),
          (174.75116408200063, -36.86094807899963)
        ]
      },
      1: {
        'centre': 'POINT (174.7426300048828 -36.86511993408203)',
        'members': [
          (174.7511328, -36.8610372),
          (174.7402083, -36.8668223),
          (174.7428788, -36.8659204)
        ]
      }
    }

.. raw:: html

   <!-- TODO find a better example -->

In the above, we have two identified clusters: - The first (``0``)
centrered at ``POINT (174.7445831298828 -36.8640251159668)``, and
another (``1``) centered at
``POINT (174.7426300048828 -36.86511993408203)``. In this case they have
an equal number of members, so the ambiguity unfortunately isn't well
resolved, but at least now you have two smaller clusters you can use,
rather than being left with a larger area of ambiguous addresses.

There are also methods to return a complete mutlipoint geometry, a
convex hull, and a concave hull of the result set.

Contributing and/or developing
==============================

Any pull requests, issues and comments are welcome. If you want to
experiment with errorgeopy with any edits you may make to it, you can
install development versions of errorgeopy from the source with, for
example:

.. code:: sh

    virtualenv -p python3 envname # Make a virtualenv with Python 3
    python setup.py sdist # Make a distribution
    pip install errorgeopy --no-index --find-links file:///path/to/errorgeopy/dist/errorgeopy-X-X-X.tar.gz # Install version X-X-X from the archive you just made

Inside ``./demo`` there is a Flask application that uses the
environment's installed version of errorgeopy for running a
demonstration.

.. |Dependencies| image:: https://www.versioneye.com/user/projects/5775cea668ee070047f065e4/badge.svg?style=flat-square
.. |PyPI version| image:: https://badge.fury.io/py/errorgeopy.svg
   :target: https://pypi.python.org/pypi/errorgeopy
.. |Build status| image:: https://api.travis-ci.org/alpha-beta-soup/errorgeopy.svg
