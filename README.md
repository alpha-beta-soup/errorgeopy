# errorgeopy
Python geocoding in a disagreeing world

<!-- pandoc --from=markdown --to=rst --output=README.rst README.md -->

![Dependencies](https://www.versioneye.com/user/projects/5775cea668ee070047f065e4/badge.svg?style=flat-round) [![PyPI version](https://badge.fury.io/py/errorgeopy.svg)](https://pypi.python.org/pypi/errorgeopy) ![Build status](https://api.travis-ci.org/alpha-beta-soup/errorgeopy.svg)
<!-- [![Coverage Status](https://coveralls.io/repos/github/alpha-beta-soup/errorgeopy/badge.svg?branch=master)](https://coveralls.io/github/alpha-beta-soup/errorgeopy?branch=master) -->

Wraps [geopy](https://github.com/geopy/geopy) geocoding to expose a simple way to use multiple providers of geocoding services simultaneously (with `multiprocessing`), and provide a report of the ensuing spatial uncertainty in the final location.

0. Configure your desired/allowed geocoding providers (`config.yml`).
1. Geocode an address using the errorgeopy `geocode` wrapper.
2. Recieve a multipoint of the geocoded address locations, the [convex hull](http://scipy.github.io/devdocs/generated/scipy.spatial.ConvexHull.html) of the result locations, the [concave hull](http://blog.thehumangeo.com/2014/05/12/drawing-boundaries-in-python/) of the results, various types of centroid, and quantitative measures of spatial agreement across component providers---as well as maintaining access to the original results.

# Installation

Requires Python 3; only tested with Python 3.4

`pip install errorgeopy`

## Dependencies

- `geopy`
- `shapely` (outputs generally are `shapely.geometry` types in geographic coordinates, to get that sweet `__geo_interface__`)
- `scikit-learn` (cluster detection)
- `scipy` (for Delaunay triangulation for concave hulls)

![Delaunay circumcircles](docs/img/delaunay-circumcircles.png)

# Why?

Geocoding is very hard, although consumer-grade APIs make the process seem very easy. Intuitively, it does seem easy: address goes in, point comes out. [That's what Osaka Seafood Concern is all about. Every truckload of addresses you geocode brings you 31 cents closer to those tickets home!](https://www.youtube.com/watch?v=cIosb69x9iI)

But what if two different geocoding services both claim a successful address-level match, but the output location is different? If it is a subtle difference, it probably doesn't matter, especially if both addresses are within the same parcel. If it is a significant difference, it is possible that the two services have identified an ambiguity in the input address, or that one of them is just wrong, or that one of them can only match down to the suburb, and not the street or numberered address. Using more services may help you identify such a situtation and ignore such "minority opinions". **This is exactly what errorgeopy can do for you.**

For example, given a configuration (not shown) for making requests to multiple geocoding services, errorgeopy can return identified clusters of addresses, in order, with the first cluster being the largest (and therefore most likely positive match):

```python
>>> import os, yaml
>>> from errorgeopy.geocoders import GeocoderPool
>>> # Get geocoder configuration from a file
>>> config = './configuration.yml'
>>> g_pool = GeocoderPool.fromfile(config, yaml.load)
>>> test = '66 Great North Road, Grey Lynn, Auckland, New Zealand'
>>> location = g_pool.geocode(test)
>>> for cl in location.clusters:
>>>     print(
>>>         'CENTRE: %s\n' % cl['centre'].wkt,
>>>         'MEMBERS: %s' % cl['members'].wkt
>>>     )
CENTRE: POINT Z (174.7384643554688 -36.86515808105469 0)
MEMBERS: MULTIPOINT Z (174.7375733 -36.8654 0, 174.7402083 -36.8668223 0, 174.7428788 -36.8659204 0, 174.7428788 -36.8659204 0, 174.7432 -36.863 0, 174.7173 -36.86803 0, 174.7511328 -36.8610372 0, 174.7511640820006 -36.86094807899963 0)
CENTRE: POINT Z (174.7366638183594 -36.86574554443359 0)
MEMBERS: POINT Z (174.7325854 -36.8651064 0)
```

<!-- TODO find a better example -->

In the above, we have two identified clusters:
- The first (`0`) centrered at `POINT Z (174.7384643554688 -36.86515808105469 0)`, and another (`1`) centered at `POINT Z (174.7366638183594 -36.86574554443359 0)`. A clustering algorithm has determined that the full set of results could be split into these two groups, and because the first group is larger than the second, it might be sensible for you to ignore the second location that the majority of input geocoders did not consider the best match.

There are also methods to return a complete mutlipoint geometry, a convex hull, and a concave hull of the result set.

# Contributing and/or developing

Any pull requests, issues and comments are welcome. If you want to experiment with errorgeopy with any edits you may make to it, you can install development versions of errorgeopy from the source with, for example:

```sh
virtualenv -p python3 envname # Make a virtualenv with Python 3
python setup.py sdist # Make a distribution
pip install errorgeopy --no-index --find-links file:///path/to/errorgeopy/dist/errorgeopy-X-X-X.tar.gz # Install version X-X-X from the archive you just made
```

Inside `./demo` there is a Flask application that uses the environment's installed version of errorgeopy for running a demonstration.

## Features

- [x] **alpha** (≤ **v0.3**) and [ ] **beta** (**v0.4**)
  - [x] Basic premise implementation: wrapping calls to multiple geocoding proiders (anything supported by geopy forward geocoding)
  - [x] Available on PiPy
  - [x] Simple geometric operations on candidate addresses
    - Centroids
    - K-means clustering
    - Smallest bounding circle
    - Convex hull
    - Concave hull
    - Use of shapely as implementation of `__geo_interface__` for Python objects

- [ ] **v1.0**
  - [x] Unit testing (using `tox` and `pytest`)
  - [x] Centroids of `Location`
  - [x] Implementing `__geo_interface__` for a `Location.cluster` property
  - [x] Reverse geocoding, with string similarity algorithms as an optional reporting tool to gauge agreement, cluster, and attempt to identify the "most complete" address (http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/)
  - [ ] Cleaner implementation of k-means clustering (better response object for cluster)
  - [ ] Documentation on readthedocs.io, built from source code
- [ ] **v1.1**
  - [ ] Hierarchical clustering
    - Still only a vague idea in my mind
    - http://varianceexplained.org/r/kmeans-free-lunch/
    - https://en.wikipedia.org/wiki/Hierarchical_clustering
    - http://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html
    - Method to return a topological [dendrogram](http://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.dendrogram.html#scipy.cluster.hierarchy.dendrogram) of the clusters (from centre of all, branching to local centres, and finally to the leaves (actual addresses returned from services), as a geographical feature that can readily be plotted on a map

## Testing

Requires [tox](http://tox.readthedocs.io/en/latest/install.html).

```
sudo tox
```
