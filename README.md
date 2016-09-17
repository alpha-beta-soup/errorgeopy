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

For example, by making requests to *multiple geocoding services*, errorgeopy can return identified clusters of addresses, in order, with the first cluster being the largest:

```python
>>> from errorgeopy.geocoders import GeocoderPool
>>> # Optionally, can also get geocoder configuration from a file, or a dict
>>> g_pool = GeocoderPool() # Use default, free, no sign-up geocoding APIs
>>> test = 'High Street, Lower Hutt, New Zealand'
>>> location = g_pool.geocode(test)
>>> for cl in location.clusters:
>>>    print(cl)
[
  Cluster(
    label=0,
    centroid=<shapely.geometry.point.Point object at 0x7fb1f99c8358>,
    geom=<shapely.geometry.multipoint.MultiPoint object at 0x7fb1f9a1a668>,
    location=[
      Location(High Street, Taita, Lower Hutt, Lower Hutt City, Wellington, 5011, New Zealand, (-41.166847, 174.9673, 0.0))
      Location(High Street, Boulcott, Lower Hutt, Lower Hutt City, Wellington, 5040, New Zealand, (-41.2034803, 174.9215726, 0.0))
      Location(High Street, Avalon, Lower Hutt, Lower Hutt City, Wellington, 5011, New Zealand, (-41.1890827, 174.9522785, 0.0))
      Location(High Street, Lower Hutt Central, Lower Hutt, Lower Hutt City, Wellington, 5010, New Zealand, (-41.2119292, 174.8996589, 0.0))
    ]
  ),

  Cluster(
    label=1,
    centroid=<shapely.geometry.point.Point object at 0x7fb1f99de710>,
    geom=<shapely.geometry.multipoint.MultiPoint object at 0x7fb1f99de240>,
    location=[
      Location(High Street, Petone, Lower Hutt, Lower Hutt City, Wellington, 5012, New Zealand, (-41.2250375, 174.8894697, 0.0))
      Location(High Street, Boulcott, Lower Hutt, Lower Hutt City, Wellington, 5010, New Zealand, (-41.2038771, 174.9165404, 0.0))
      Location(High Street, Lower Hutt Central, Lower Hutt, Lower Hutt City, Wellington, 5010, New Zealand, (-41.2067898, 174.9079979, 0.0))
      Location(High St, Lower Hutt, 5010, (-41.20740676599962, 174.9066761100006, 0.0))
    ]
  ),

  Cluster(
    label=2,
    centroid=<shapely.geometry.point.Point object at 0x7fb1f9a29d30>,
    geom=<shapely.geometry.multipoint.MultiPoint object at 0x7fb1f99db198>,
    location=[
      Location(High Street, Manor Park, Lower Hutt, Lower Hutt City, Wellington, 5011, New Zealand, (-41.1662641, 174.9716431, 0.0))
    ]
  )
]
```

<!-- TODO find a better example -->

In the above, we have three identified clusters. If you know your input to be well-specified, then you might pick the larger groups, and disregard the cluster with only one member. In this case, we just have a vague input, and so should embrace the vagueness of our result. A single geocoding service with a vague input address would be considerably more constrained than this result.

There are also methods to return a complete mutlipoint geometry, a convex hull, a concave hull of the result set.

Reverse geocoding is also supported, including the ability to "seed" the result with a string that the results are scored against using fuzzy string matching. You can also obtain the longest common substring. (I'm sure there's much more that can be done with matching address string, let me know if you have an idea.)

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
