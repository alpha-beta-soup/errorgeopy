# errorgeopy
Python geocoding in a disagreeing world

Wraps [geopy](https://github.com/geopy/geopy) geocoding to expose a simple way to use multiple providers of geocoding services simultaneously (with `multiprocessing`), and provide a report of the ensuing spatial uncertainty in the final location.

0. Configure your desired/allowed geocoding providers (`config.yml`).
1. Geocode an address using the errorgeopy `geocode` wrapper.
2. Recieve a multipoint of the geocoded address locations, the [convex hull](http://scipy.github.io/devdocs/generated/scipy.spatial.ConvexHull.html) of the result locations, the [concave hull](http://blog.thehumangeo.com/2014/05/12/drawing-boundaries-in-python/) of the results, various types of centroid, and quantitative measures of spatial agreement across component providers---as well as maintaining access to the original results.

<!-- TODO how to install and contribute fixes and improvements -->
# Contributing and/or developing

Any pull requests, issues and comments are welcome. If you want to experiment with errorgeopy with any edits you may make to it, you can install development versions of errorgeopy from the source with, for example:

```sh
virtualenv -p python3 envname # Make a virtualenv with Python 3
python setup.py sdist # Make a distribution
pip install errorgeopy --no-index --find-links file:///path/to/errorgeopy/dist/errorgeopy-X-X-X.tar.gz # Install version X-X-X from the archive you just made
```

Inside `./demo` there is a Flask application that uses the environment's installed version of errorgeopy for running a demonstration.
