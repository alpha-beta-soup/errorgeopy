import numpy as np

from shapely.geometry import Point, Polygon
from scipy.spatial import Delaunay
from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.preprocessing import Imputer

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

def get_clusters(pts, bandwidth=None):
    '''Returns one or more clusters of a set of points
    The result is sorted with the first value being the largest cluster.
    Uses a mean-shift clustering algorithm.
    If bandwidth is None, a value is detected automatically
    from the input using estimate_bandwidth'''
    if not pts:
        return None
    X = np.array(pts)
    assert not np.any(np.isnan(X))
    assert np.all(np.isfinite(X))
    X = Imputer().fit_transform(X)
    X = X.astype(np.float32)
    print(X)
    # print(X)
    # # from sklearn.utils.validation import _assert_all_finite
    # # assert _assert_all_finite(X)
    # if (X.dtype.char in np.typecodes['AllFloat'] and not np.isfinite(X.sum())
    #         and not np.isfinite(X).all()):
    #     raise ValueError("Input contains NaN, infinity"
    #             " or a value too large for %r." % X.dtype)
    # import time
    # print("yeah")
    # time.sleep(5)
    # assert not ((X.dtype.char in np.typecodes['AllFloat'] and not np.isfinite(X.sum()) and not np.isfinite(X).all()))
    if not bandwidth:
        bandwidth = estimate_bandwidth(X, quantile=0.3)
    ms = MeanShift(bandwidth=bandwidth or None, bin_seeding=False)
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
            clusters[i]['members'].append(pts[j])
    return clusters