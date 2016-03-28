[![Build Status](https://travis-ci.org/alpha-beta-soup/errorgeopy.svg?branch=master)](https://travis-ci.org/alpha-beta-soup/errorgeopy)

# errorgeopy
Python geocoding in a disagreeing world

Wraps [geopy](https://github.com/geopy/geopy) geocoding to expose a simple way to use multiple providers of geocoding services simultaneously, and provide a report of the insuing spatial uncertainty in the final location.

0. Configure your desired/allowed geocoding providers (`errorgeopy.yml`).
1. Geocode an address using the errorgeopy `geocode` wrapper.
2. Recieve a multipoint of the geocoded address locations, the [convex hull] of the rsult, the [concave hull](http://blog.thehumangeo.com/2014/05/12/drawing-boundaries-in-python/) of the result, various types of centroid, and quantititative measures of spatial agreeement across component providers.
