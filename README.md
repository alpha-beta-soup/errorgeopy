# errorgeopy
Python geocoding in a disagreeing world

Wraps [geopy](https://github.com/geopy/geopy) geocoding to expose a simple way to use multiple providers of geocoding services simultaneously, and provide a report of the ensuing spatial uncertainty in the final location.

0. Configure your desired/allowed geocoding providers (`config.yml`).
1. Geocode an address using the errorgeopy `geocode` wrapper.
2. Recieve a multipoint of the geocoded address locations, the [convex hull](http://scipy.github.io/devdocs/generated/scipy.spatial.ConvexHull.html) of the result locations, the [concave hull](http://blog.thehumangeo.com/2014/05/12/drawing-boundaries-in-python/) of the results, various types of centroid, and quantitative measures of spatial agreement across component providers---as well as maintaining access to the original results.

<!-- TODO how to install and contribute fixes and improvements -->
