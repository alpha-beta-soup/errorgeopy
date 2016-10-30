"""Utility functions for ErrorGeoPy. Inteded to be private functions, their
call signatures are not considered strictly static.

.. moduleauthor Richard Law <richard.m.law@gmail.com>
"""

import numpy as np
from collections import namedtuple
from functools import partial, wraps
from itertools import compress
import inspect

import geopy
from geopy.point import Point as GeopyPoint
from shapely.geometry import Point, MultiPoint, Polygon
from scipy.spatial import Delaunay
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import MeanShift, AffinityPropagation, DBSCAN, estimate_bandwidth
from sklearn.preprocessing import Imputer, StandardScaler
from sklearn import metrics
from sklearn.metrics.pairwise import euclidean_distances
import pyproj

from errorgeopy.smallestenclosingcircle import make_circle


def check_location_type(func):
    """Decorator for checking that the first argument of a function is an array
    of geopy.Location objects. Raises ValueError is this condition is not met.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        if not all(map(lambda x: isinstance(x, geopy.Location), args[1])):
            raise ValueError
        else:
            return func(*args, **kwargs)

    return inner


def check_addresses_exist(func):
    """Decorator for checking that the first argument of a function has an
    addresses property
    """

    @wraps(func)
    def inner(*args, **kwargs):
        if not args[0].addresses:
            return None
        else:
            return func(*args, **kwargs)

    return inner


def geopy_point_to_shapely_point(point):
    """Converts a geopy.point.Point to a shapely.geometry.Point.

    Args:
        point (geopy.point.Point)
    """
    if not isinstance(point, GeopyPoint):
        raise TypeError
    return Point(point.longitude, point.latitude, point.altitude)


def array_geopy_points_to_shapely_points(points):
    """Converts an array of geopy.point.Point objects to an array of
    shapely.geometry.Point objects.

    Args:
        points (sequence of geopy.point.Point objects)
    """
    return [geopy_point_to_shapely_point(p) for p in points]


def array_geopy_points_to_xyz_tuples(points):
    """Converts an array of geopy.point.Point objects to an array of
    (x, y, z) tuples.

    Args:
        points (sequence of geopy.point.Point objects)
    """
    return [geopy_point_to_shapely_point(p).coords[0] for p in points]


def sq_norm(v):
    return np.linalg.norm(v)**2


def circumcircle(points, simplex):
    """Computes the circumcentre and circumradius of a triangle:
    https://en.wikipedia.org/wiki/Circumscribed_circle#Circumcircle_equations
    """
    A = [points[simplex[k]] for k in range(3)]
    M = np.asarray([[1.0] * 4] +
                   [[sq_norm(A[k]), A[k][0], A[k][1], 1.0] for k in range(3)],
                   dtype=np.float32)
    S = np.array([0.5 * np.linalg.det(M[1:, [0, 2, 3]]),
                  -0.5 * np.linalg.det(M[1:, [0, 1, 3]])])
    a = np.linalg.det(M[1:, 1:])
    b = np.linalg.det(M[1:, [0, 1, 2]])
    centre, radius = S / a, np.sqrt(b / a + sq_norm(S) / a**2)
    return centre, radius


def get_alpha_complex(alpha, points, simplexes):
    """Obtain the alpha shape.

    Args:
        alpha (float): the paramter for the alpha shape
        points: data points
        simplexes: the list of indices that define 2-simplexes in the Delaunay
            triangulation
    """
    return filter(lambda simplex: circumcircle(points, simplex)[1] < alpha,
                  simplexes)


def concave_hull(points, alpha, delunay_args=None):
    """Computes the concave hull (alpha-shape) of a set of points.
    """
    delunay_args = delunay_args or {
        'furthest_site': False,
        'incremental': False,
        'qhull_options': None
    }
    triangulation = Delaunay(np.array(points))
    alpha_complex = get_alpha_complex(alpha, points, triangulation.simplices)
    X, Y = [], []
    for s in triangulation.simplices:
        X.append([points[s[k]][0] for k in [0, 1, 2, 0]])
        Y.append([points[s[k]][1] for k in [0, 1, 2, 0]])
    poly = Polygon(list(zip(X[0], Y[0])))
    for i in range(1, len(X)):
        poly = poly.union(Polygon(list(zip(X[i], Y[i]))))
    return poly


def point_nearest_point(points, point):
    """Returns the shapely.geometry.Point in <points> that is nearest <point>.
    """
    distances = [point.distance(p) for p in points]
    return points[distances.index(min(distances))]


def cross(o, a, b):
    """2D cross product of OA and OB vectors, i.e. z-component of their 3D cross
    product.

    Returns:
        A positive value, if OAB makes a counter-clockwise turn,
        negative for clockwise turn, and zero if the points are collinear.
    """
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


# https://en.wikibooks.org/wiki/Algorithm_Implementation/Geometry/Convex_hull/Monotone_chain#Python
def convex_hull(points):
    """Computes the convex hull of a set of 2D points.

    Takes an iterable sequence of hashable (x, y, ...) tuples representing the
    points. Only the (x, y) pairs are used, so output is in two-dimensions.
    Outputs a shapely.geometry.Polygon representing the convex hull, in
    counter-clockwise order, starting from the vertex with the lexicographically
    smallest coordinates. Implements Andrew's monotone chain algorithm.
    O(n log n) complexity.
    """
    # Convert, sort the points lexicographically, and remove duplicates
    points = sorted(set(points))
    if len(points) <= 1:
        return points

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
    # Last point of each list is omitted because it is repeated at the
    # beginning of the other list.
    # Input to Polygon is a list of vertices in counter-clockwise order,
    # starting at the point with the lexicographically smallest coordinates
    return Polygon(lower[:-1] + upper[:-1])


def minimum_bounding_circle(points):
    """Returns the minimum bounding circle of a set of points as a
    shapely.geometry.Polygon (64-sided polygon approximating a circle)
    """
    # TODO using cartesian coordinates, not geographic
    mbc = make_circle(points)
    if not mbc:
        return None
    x, y, radius = mbc
    return Point(x, y).buffer(radius)


def cluster_named_tuple():
    """Defines a NamedTuple representing a single cluster.

    Returns:
        Named tuple with the following properties:
            label (int): the id of the cluster
            centroid: Point representing the cluster centre
            geom (MultiPoint or Point): the cluster members
            location (errorgeopy.Location): one cluster from the input set
    """
    return namedtuple('Cluster', ['label', 'centroid', 'location'])


def mean_shift(location, location_callback, bandwidth=None):
    """Returns one or more clusters of a set of points, using a mean shift
    algorithm.
    The result is sorted with the first value being the largest cluster.

    Kwargs:
        bandwidth (float): If bandwidth is None, a value is detected
        automatically from the input using estimate_bandwidth.

    Returns:
        A list of NamedTuples (see get_cluster_named_tuple for a definition
        of the tuple).
    """
    pts = location._tuple_points()
    if not pts:
        return None
    X = np.array(pts)
    if np.any(np.isnan(X)) or not np.all(np.isfinite(X)):
        return None
    X = Imputer().fit_transform(X)
    X = X.astype(np.float32)
    if not bandwidth:
        bandwidth = estimate_bandwidth(X, quantile=0.3)
    ms = MeanShift(bandwidth=bandwidth or None, bin_seeding=False).fit(X)
    clusters = []
    for cluster_id, cluster_centre in enumerate(ms.cluster_centers_):
        locations = []
        for j, label in enumerate(ms.labels_):
            if not label == cluster_id:
                continue
            locations.append(location.locations[j])
        if not locations:
            continue
        clusters.append(cluster_named_tuple()(label=cluster_id,
                                              centroid=Point(cluster_centre),
                                              location=location_callback(
                                                  locations)))
    return clusters


def affinity_propagation(location, location_callback):
    """Returns one or more clusters of a set of points, using an affinity
    propagation algorithm.
    The result is sorted with the first value being the largest cluster.

    Returns:
        A list of NamedTuples (see get_cluster_named_tuple for a definition
        of the tuple).
    """
    pts = location._tuple_points()
    if not pts:
        return None
    X = np.array(pts)
    if np.any(np.isnan(X)) or not np.all(np.isfinite(X)):
        return None
    X = Imputer().fit_transform(X)
    X = X.astype(np.float32)
    afkwargs = {
        'damping': 0.5,
        'convergence_iter': 15,
        'max_iter': 200,
        'copy': True,
        'preference': None,
        'affinity': 'euclidean',
        'verbose': False
    }
    af = AffinityPropagation(**afkwargs).fit(X)
    cluster_centers_indices = af.cluster_centers_indices_
    clusters = []
    for cluster_id, cluster_centre in enumerate(af.cluster_centers_):
        locations = []
        for j, label in enumerate(af.labels_):
            if not label == cluster_id:
                continue
            locations.append(location.locations[j])
        if not locations:
            continue
        clusters.append(cluster_named_tuple()(label=cluster_id,
                                              centroid=Point(cluster_centre),
                                              location=location_callback(
                                                  locations)))
    return clusters


def dbscan(location, location_callback, core_only=False, epsilon=1, **kwargs):
    """Returns one or more clusters of a set of points, using a DBSCAN
    algorithm.
    The result is sorted with the first value being the largest cluster.

    Returns:
        A list of NamedTuples (see get_cluster_named_tuple for a definition
        of the tuple).

    Notes:
        This implementation is not strictly correct (improved method explained
            here http://geoffboeing.com/2014/08/clustering-to-reduce-spatial-data-set-size/),
            but good enough for now.
        The centre of a cluster computed with DBSCAN is not meaningful (because
            they are irregularly-shaped), so centroids are determined as a point
            in the cluster that is nearest the geometric centre of the cluster,
            rather than merely the geometric centre.
    """
    pts = [p[0:2] for p in location._tuple_points()]
    if not pts or len(pts) == 1:
        return None
    pts = np.array(pts)
    # print(pts, pts.shape, pts.reshape(-1, 1), pts.reshape(1, -1))
    # if 1 in pts.shape:
    #     print(pts.shape, pts)
    #     pts = [pts]
    X = squareform(pdist(pts, metric='cityblock'))
    if np.any(np.isnan(X)) or not np.all(np.isfinite(X)):
        return None
    # X = np.radians(X
    X = StandardScaler().fit_transform(X)
    dbkwargs = {
        'eps': epsilon,
        'min_samples': 1,
        'metric': euclidean_distances,
        # 'metric': 'haversine',
        'algorithm': 'brute',
        'leaf_size': None
    }
    db = DBSCAN(**dbkwargs).fit(X)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    unique_labels = set(labels)
    clusters = []
    for k in unique_labels:
        class_member_mask = (labels == k)
        if k == -1:
            # Noise
            continue
        _filter = class_member_mask if not core_only else class_member_mask & core_samples_mask
        _pts = list(map(Point, pts[_filter]))
        centroid = MultiPoint(_pts).centroid
        if len(pts) == 0 and _pts == centroid:
            centroid = _pts[0]
        else:
            get_dist = lambda x: x.distance(centroid)
            distances = list(map(get_dist, _pts))
            centroid = _pts[distances.index(min(distances))]
        clusters.append(cluster_named_tuple()(label=k,
                                              centroid=centroid,
                                              location=location_callback(list(
                                                  compress(location.locations,
                                                           _filter)))))
    return clusters


def get_clusters(location, location_callback, method=dbscan, **kwargs):
    return method(location, location_callback, **kwargs)


def long_substr(data):
    """Find the longest substring, given a sequence of strings."""
    if not data:
        return None
    if len(data) == 1:
        return data[0]
    substr = ''
    for i in range(len(data[0])):
        for j in range(len(data[0]) - i + 1):
            if j > len(substr) and all(data[0][i:i + j] in x for x in data):
                substr = data[0][i:i + j]
    return substr.strip()


def get_proj(epsg):
    """Returns a pyproj partial representing a projedction from WGS84 to
    a given projection.

    Args:
        epsg: EPSG code for the target projection.
    """
    project = partial(pyproj.transform,
                      pyproj.Proj(init='EPSG:4326'),
                      pyproj.Proj(init='EPSG:{epsg}'.format(epsg=epsg)))
