import geopy
from shapely.geometry import MultiPoint, GeometryCollection

from errorgeopy import utils


def check_points_exist(func):
    '''Decorator for checking that the first argument of a function has an
    _addresses property
    '''

    def inner(*args, **kwargs):
        if args[0].points is None:
            return None
        else:
            return func(*args, **kwargs)

    return inner


def check_polygonisable(func):
    def inner(*args, **kwargs):
        if not args[0]._polygonisable():
            return None
        else:
            return func(*args, **kwargs)

    return inner


def check_concave_hull_calcuable(func):
    '''Decorator for checking that there are enough candidates to compute a
    concave hull.
    '''

    def inner(*args, **kwargs):
        if len(args[0]) < 4:
            return None
        else:
            return func(*args, **kwargs)

    return inner


def check_convex_hull_calcuable(func):
    '''Decorator for checking that there are enough candidates to compute a
    concave hull.
    '''

    def inner(*args, **kwargs):
        if len(args[0]) < 3:
            return None
        else:
            return func(*args, **kwargs)

    return inner


def check_cluster_calculable(func):
    def inner(*args, **kwargs):
        if len(args[0]._location) < 3:
            return []
        else:
            return func(*args, **kwargs)

    return inner


# TODO it'd be nice to have the names of the geocoder that produced each cluster member; this would require extending geopy.Location to include this information
class LocationClusters(object):
    def __init__(self, location):
        '''
        Represents clusters of addresses identified from an input
        errorgeopy.Location object
        '''
        self._location = location

    @property
    @check_cluster_calculable
    def clusters(self):
        '''
        Returns clusters, else an empty array
        '''
        return utils.get_clusters(self._location, Location)

    def __len__(self):
        return len(self.clusters)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '\n'.join([str(c.location) for c in self.clusters])

    def __getitem__(self, index):
        return self.clusters[index]

    def geometry_collection(self):
        # TODO don't use the private property of location
        return GeometryCollection([c.geom for c in self.clusters])

    def cluster_centres(self):
        return MultiPoint([c.centroid for c in self.clusters])


class Location(object):
    @utils.check_location_type
    def __init__(self, locations):
        '''
        Contains an array of parsed geocoder responses, each of which are
        geopy.Location objects.
        '''
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
        if not isinstance(self._locations, list):
            return [self._locations]
        else:
            return self._locations

    @property
    def addresses(self):
        '''
        Convenience method to get geopy.Location.address properties for all
        candidate locations as an array
        '''
        return [l.address for l in self.locations]

    @property
    def points(self):
        '''
        Returns an array of geopy.Point objects representing the candidate
        locations. These are geodetic points, with latitude, longitude, and
        altitude (in kilometres), default 0.
        '''
        return [l.point for l in self.locations]

    def _shapely_points(self):
        return utils.array_geopy_points_to_shapely_points(self.points)

    def _tuple_points(self):
        return utils.array_geopy_points_to_xyz_tuples(self.points)

    @property
    @check_points_exist
    def multipoint(self):
        '''
        Returns a shapely.geometry.MultiPoint of the Location
        '''
        return MultiPoint(self._shapely_points())

    @property
    @check_points_exist
    def centroid(self):
        '''
        Returns a shapely.geometry.Point of the centre of all candidate address
        locations
        '''
        return self.multipoint.centroid

    @property
    @check_points_exist
    def mbc(self):
        '''
        Returns a shapely.geometry.Polygon representing the minimum bounding
        circle of the candidate locations
        '''
        return utils.minimum_bounding_circle(
            [p[0:2] for p in self._tuple_points()])

    @property
    @check_concave_hull_calcuable
    @check_polygonisable
    def concave_hull(self, alpha=0.15):
        '''
        Returns a concave hull of the Location, as a shapely.geometry.Polygon
        object. Needs at least four candidates to function, else returns None.
        '''
        return utils.concave_hull([p[0:2] for p in self._tuple_points()],
                                  alpha)

    @property
    @check_convex_hull_calcuable
    @check_polygonisable
    def convex_hull(self):
        '''
        Returns a convex hull of the Location, as a shapely.geometry.Polygon
        object. Needs at least three candidates to function, else returns None.
        '''
        return utils.convex_hull(self._tuple_points())

    @property
    @check_points_exist
    def clusters(self):
        '''
        Returns clusters that have been identified in the Location's candidate
        addresses
        '''
        # TODO document and maybe sub-class the return value
        return LocationClusters(self)
