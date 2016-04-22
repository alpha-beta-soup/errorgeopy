import os
import copy
import itertools

import yaml
import geopy
import numpy as np
from shapely.geometry import Point, Polygon, MultiPoint
from scipy.spatial import Delaunay
from sklearn.cluster import MeanShift, estimate_bandwidth

def sq_norm(v):
    '''Squared norm'''
    return np.linalg.norm(v)**2

def circumcircle(points, simplex):
    '''Computes the circumcentre and circumradius of a triangle:
    https://en.wikipedia.org/wiki/Circumscribed_circle#Circumcircle_equations
    '''
    A = [points[simplex[k]] for k in range(3)]
    M = np.asarray(
        [[1.0]*4] + [[sq_norm(A[k]), A[k][0], A[k][1], 1.0] for k in range(3)],
        dtype=np.float32
    )
    S = np.array(
        [0.5*np.linalg.det(M[1:,[0,2,3]]), -0.5*np.linalg.det(M[1:,[0,1,3]])]
    )
    a = np.linalg.det(M[1:,1:])
    b = np.linalg.det(M[1:,[0,1,2]])
    centre, radius = S/a, np.sqrt(b/a+sq_norm(S)/a**2)
    return centre, radius

def get_alpha_complex(alpha, points, simplexes):
    '''
    alpha: the paramter for the alpha shape
    points: data points
    simplexes: the list of indices that define 2-simplexes in the Delaunay
               triangulation
    '''
    return filter(
        lambda simplex: circumcircle(points, simplex)[1]<alpha, simplexes
    )

def concave_hull(points, alpha):
    delunay_args = {
        'furthest_site': False,
        'incremental': False,
        'qhull_options': None
    }
    triangulation = Delaunay(np.array(points))
    alpha_complex = get_alpha_complex(
        alpha, points, triangulation.simplices
    )
    X, Y = [], []
    for s in triangulation.simplices:
        X.append([points[s[k]][0] for k in [0,1,2,0]])
        Y.append([points[s[k]][1] for k in [0,1,2,0]])
    poly = Polygon(list(zip(X[0],Y[0])))
    for i in range(1,len(X)):
        poly = poly.union(Polygon(list(zip(X[i],Y[i]))))
    return poly

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
    return Polygon(lower[:-1] + upper[:-1])

class Geocoder(object):
    def __init__(self, geocoder_name, config):
        self._class = geopy.get_geocoder_for_service(geocoder_name)
        self.geocode_kwargs = config.pop('geocode') if config.get('geocode', None) else {}
        self.reverse_kwargs = config.pop('reverse') if config.get('reverse', None) else {}
        self.geocoder = self._class(**config)
        self.name = geocoder_name

class Geocoders(object):
    def __init__(self, config):
        self.config = config
        if not isinstance(self.config, dict):
            raise NotImplementedError
        self.geocoders = self.get_geocoders()
        self.pts = None
        self.convex_hull = None
        self.concave_hull = None
        self.multipoint = None
        self.is_polygonisable = None

    def _get_points_from_resultset(self, results):
        if not results:
            self.is_polygonisable = False
            return None
        if not isinstance(results, list):
            results = [results]
        self.is_polygonisable = True if len(results) > 2 else False
        return [(r.longitude, r.latitude,) for r in results]

    def geocode(self, query):
        results = []
        for geocoder in self.geocoders:
            try:
                result = geocoder.geocoder.geocode(query, **geocoder.geocode_kwargs)
            except geopy.exc.GeocoderTimedOut as timeout:
                print(geocoder.name, timeout)
                continue
            if not result:
                print(geocoder.name, 'no result')
                continue
            for res in result:
                if not res:
                    continue
                print(geocoder.name, repr(res))
                results.append(res)
        self.pts = self._get_points_from_resultset(results)
        return results

    def get_geocoders(self):
        return [Geocoder(gc, self.config[gc]) for gc in self.config]

    def get_multipoint(self):
        if not self.pts:
            return None
        return MultiPoint(self.pts)

    def get_clusters(self, bandwidth=None):
        '''Returns one or more clusters of result addresses, or None if there
        are no results. The members of the returned array of Cluster object
        include the constiuent addresses, and the result is sorted with the
        first value being the largest cluster. Uses a mean-shift clustering
        algorithm. If bandwidth is None, a value is detected automatically
        from the input using estimate_bandwidth'''
        if not self.pts:
            return None
        X = np.array(self.pts)
        if not bandwidth:
            bandwidth = estimate_bandwidth(X, quantile=0.3)
        ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
        ms.fit(X)
        labels = ms.labels_
        cluster_centres = ms.cluster_centers_
        clusters = {} # TODO replace with actual object, refactor
        for i, cc in enumerate(ms.cluster_centers_):
            clusters[i] = {}
            clusters[i]['centre'] = Point(cc).wkt
            clusters[i]['members'] = []
            for j, label in enumerate(labels):
                if not label == i:
                    continue
                clusters[i]['members'].append(self.pts[j])
        print("Estimated clusters: %d" % len(clusters))
        return clusters

    def get_concave_hull(self, alpha=0.15):
        if not self.is_polygonisable:
            return None
        return concave_hull(self.pts, alpha)

    def get_convex_hull(self):
        if not self.is_polygonisable:
            return None
        return convex_hull(self.pts)


if __name__ == '__main__':
    config = os.path.abspath(os.path.join(
        os.path.dirname( __file__ ), '..', 'configuration.yml'
    ))
    with open(config, 'r') as geocoders:
        gcs = Geocoders(yaml.load(geocoders))
        test = '66 Great South Road, Auckland, New Zealand'
        result = gcs.geocode(test)
        print(gcs.get_convex_hull().wkt)
        print(gcs.get_concave_hull().wkt)
        print(gcs.get_multipoint().wkt)
        print(gcs.get_clusters())
