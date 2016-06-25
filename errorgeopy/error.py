import numpy as np

from shapely.geometry import Point
from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.preprocessing import Imputer

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
