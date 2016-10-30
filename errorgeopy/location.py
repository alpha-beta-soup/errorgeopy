"""A "Location" is a collecion of responses from geocoding services, each one a
distinct attempt to either find a string address given a point (reverse geocode)
or an attempt to find a point that best matches a string address (forward
geocode). A Location is a collection, because fundamentally *ErrorGeoPy* is
oriented to working across providers, and considering all of their results as a
related set of responses.

A "LocationClusters" object, also defined here, is also a collection of
addresses. but is slightly less abstract in that the members of the collection
are organised into clusters, based on some clustering algorithm.

Heavy use is made of shapely in return values of methods for these classes.

.. moduleauthor Richard Law <richard.m.law@gmail.com>
"""

from functools import wraps

import geopy
from shapely.geometry import MultiPoint, GeometryCollection
from shapely.ops import transform

from errorgeopy import utils


def _check_points_exist(func):
    """Decorator for checking that the first argument of a function has a
    points property.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        if not args[0].points:
            return None
        else:
            return func(*args, **kwargs)

    return inner


def _check_polygonisable(func):
    """Decorator for checking that the first argument of a function has a method
    called "_polgonisable" that takes no methods, and returns True.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        if not args[0]._polygonisable():
            return None
        else:
            return func(*args, **kwargs)

    return inner


def _check_concave_hull_calcuable(func):
    """Decorator for checking that there are enough candidates to compute a
    concave hull.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        if len(args[0]) < 4:
            return None
        else:
            return func(*args, **kwargs)

    return inner


def _check_convex_hull_calcuable(func):
    """Decorator for checking that there are enough candidates to compute a
    concave hull.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        if len(args[0]) < 3:
            return None
        else:
            return func(*args, **kwargs)

    return inner


def _check_cluster_calculable(func):
    """Decorator for checking that there are enough locations for calculating
    clusters (mininum of 2).
    """

    @wraps(func)
    def inner(*args, **kwargs):
        if len(args[0]._location) < 3:
            return []
        else:
            return func(*args, **kwargs)

    return inner


class Location(object):
    """Represents a collection of parsed geocoder responses, each of which
    are geopy.Location objects, representing the results of different
    geocoding services for the same query.
    """

    @utils.check_location_type
    def __init__(self, locations):
        self._locations = locations or []

    def __unicode__(self):
        return '\n'.join(self.addresses)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return '\n'.join([repr(l) for l in self._locations])

    def __getitem__(self, index):
        return self._locations[index]

    def __setitem__(self, index, value):
        if not isinstance(value, geopy.Location):
            raise TypeError
        self.locations[index] = value

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False
        for l, o in zip(self.locations, other):
            if not l == o:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self._locations)

    def _polygonisable(self):
        if not self._locations or len(self.locations) <= 1:
            return False
        return True

    @property
    def locations(self):
        """A sequence of geopy.Location objects.
        """
        if not isinstance(self._locations, list):
            return [self._locations]
        else:
            return self._locations

    @property
    def addresses(self):
        """geopy.Location.address properties for all candidate locations as a
        sequence of strings.
        """
        return [l.address for l in self.locations]

    @property
    def points(self):
        """An array of geopy.Point objects representing the candidate locations
        physical positions. These are geodetic points, with latitude, longitude,
        and altitude (in kilometres, when supported by providers; defaults to 0.
        """
        return [l.point for l in self.locations]

    @property
    @_check_points_exist
    def multipoint(self):
        """A shapely.geometry.MultiPoint of the Location members.
        """
        return MultiPoint(self._shapely_points())

    @property
    @_check_points_exist
    def centroid(self):
        """A shapely.geometry.Point of the centre of all candidate address
        locations (centre of the multipoint).
        """
        return self.multipoint.centroid

    @property
    @_check_points_exist
    def most_central_location(self):
        """A shapely.geometry.Point representing the geometry of the candidate
        location that is nearest to the geometric centre of all of the candidate
        locations.
        """
        return utils.point_nearest_point(self._shapely_points(), self.centroid)

    @property
    @_check_points_exist
    def mbc(self):
        """A shapely.geometry.Polygon representing the minimum bounding circle
        of the candidate locations.
        """
        return utils.minimum_bounding_circle(
            [p[0:2] for p in self._tuple_points()])

    @property
    @_check_concave_hull_calcuable
    @_check_polygonisable
    def concave_hull(self, alpha=0.15):
        """A concave hull of the Location, as a shapely.geometry.Polygon object.
        Needs at least four candidates, or else this property is None.

        Kwargs:
            alpha (float): The parameter for the alpha shape
        """
        return utils.concave_hull([p[0:2] for p in self._tuple_points()],
                                  alpha)

    @property
    @_check_convex_hull_calcuable
    @_check_polygonisable
    def convex_hull(self):
        """A convex hull of the Location, as a shapely.geometry.Polygon
        object. Needs at least three candidates, or else this property is None.
        """
        return utils.convex_hull(self._tuple_points())

    @property
    @_check_points_exist
    def clusters(self):
        """Clusters that have been identified in the Location's candidate
        addresses, as an errorgeopy.location.LocationClusters object.
        """
        return LocationClusters(self)

    def _shapely_points(self, epsg=None):
        if epsg:
            projection = utils.get_proj(epsg)
            points = [transform(projection, p) for p in self.points]
        return utils.array_geopy_points_to_shapely_points(self.points)

    def _tuple_points(self, epsg=None):
        if epsg:
            projection = utils.get_proj(epsg)
            points = [transform(projection, p) for p in self.points]
        return utils.array_geopy_points_to_xyz_tuples(self.points
                                                      if not epsg else points)


# TODO it'd be nice to have the names of the geocoder that produced each cluster member; this would require extending geopy.Location to include this information
class LocationClusters(object):
    """Represents clusters of addresses identified from an errorgeopy.Location
    object, which itself is one coherent collection of respones from multiple
    geocoding services for the same query.
    """

    def __init__(self, location):
        self._location = location

    def __len__(self):
        return len(self.clusters)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '\n'.join([str(c.location) for c in self.clusters])

    def __getitem__(self, index):
        return self.clusters[index]

    @property
    @_check_cluster_calculable
    def clusters(self):
        """A sequence of clusters identified from the input. May have length 0
        if no clusters can be determined.
        """
        return utils.get_clusters(self._location, Location)

    @property
    def geometry_collection(self):
        """GeometryCollection of clusters as multipoint geometries.
        """
        return GeometryCollection(
            [c.location.multipoint for c in self.clusters])

    @property
    def cluster_centres(self):
        """Multipoint of cluster geometric centroids.
        """
        return MultiPoint([c.centroid for c in self.clusters])
