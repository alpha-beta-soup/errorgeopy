import copy
import itertools

import geopy
import numpy as np
from shapely.geometry import Polygon

GEOCODERS = {
    'nominatim': {
        # 'format_string': "%s",
        # 'view_box': None,
        # 'country_bias': 'New Zealand',
        # 'proxies': None,
        # 'timeout': None,
        # 'domain': 'nominatim.openstreetmap.org',
        # 'scheme': 'http',
        # 'user_agent': None,
        'geocode': {
            'exactly_one': False
        },
        'reverse': {
            'exactly_one': False
        }
    },
    'GeocoderDotUS': {
        'geocode': {
            'exactly_one': False
        }
    },
    'ArcGIS': {
        'geocode': {
            'exactly_one': False
        }
    },
    'databc': {
        'geocode': {
            'max_results': 25,
            'exactly_one': False
        }
    }
}

# https://en.wikibooks.org/wiki/Algorithm_Implementation/Geometry/Convex_hull/Monotone_chain#Python
def convex_hull(points):
    """Computes the convex hull of a set of 2D points.

    Input: an iterable sequence of hashable (x, y) pairs representing the points.
    Output: a list of vertices of the convex hull in counter-clockwise order,
      starting from the vertex with the lexicographically smallest coordinates.
    Implements Andrew's monotone chain algorithm. O(n log n) complexity.
    """

    # Sort the points lexicographically (tuples are compared lexicographically).
    # Remove duplicates to detect the case we have just one unique point.
    points = sorted(set(points))

    # Boring case: no points or a single point, possibly repeated multiple times.
    if len(points) <= 1:
        return points

    # 2D cross product of OA and OB vectors, i.e. z-component of their 3D cross product.
    # Returns a positive value, if OAB makes a counter-clockwise turn,
    # negative for clockwise turn, and zero if the points are collinear.
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    # Build lower hull
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenation of the lower and upper hulls gives the convex hull.
    # Last point of each list is omitted because it is repeated at the beginning of the other list.
    return lower[:-1] + upper[:-1]

class Geocoder(object):
    def __init__(self, geocoder_name, config):
        self._class = geopy.get_geocoder_for_service(geocoder_name)
        self.geocode_kwargs = config.pop('geocode') if config.get('geocode', None) else {}
        self.reverse_kwargs = config.pop('reverse') if config.get('reverse', None) else {}
        self.geocoder = self._class(**config)
        self.name = geocoder_name

class Geocoders(object):
    def __init__(self, geocoders):
        self.config = geocoders
        self.geocoders = self.get_geocoders()
        self.convex_hull = None
        self.concave_hull = None

    def get_geocoders(self):
        return [Geocoder(gc, self.config[gc]) for gc in self.config]

    def geocode(self, query):
        results = []
        for geocoder in self.geocoders:
            try:
                result = geocoder.geocoder.geocode(query, **geocoder.geocode_kwargs)
            except Exception as exc:
                print(exc)
                continue
            if not result:
                return None
            for res in result:
                results.append(res)
        self.convex_hull = self._get_convex_hull(results)
        self.concave_hull = self._get_concave_hull(results)

        return results

    def _get_concave_hull(self, results):
        return

    def _get_convex_hull(self, results):
        if not results:
            return None
        if len(results) < 3:
            return None
        pts = [(r.longitude, r.latitude,) for r in results]
        return Polygon(convex_hull(pts))


if __name__ == '__main__':
    gcs = Geocoders(GEOCODERS)
    test = 'Nelson Street, Vancouver, BC, Canada'
    result = gcs.geocode(test)
    if gcs.convex_hull:
        print(gcs.convex_hull.wkt)
