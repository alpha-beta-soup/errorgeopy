import os
import collections
import warnings
from multiprocessing.dummy import Pool as ThreadPool
from itertools import repeat

import geopy
from geopy.geocoders import Nominatim, GoogleV3 # Default GeocoderPool
from shapely.geometry import MultiPoint

import errorgeopy.utils as utils

DEFAULT_GEOCODER_POOL = [Nominatim(), GoogleV3()]

def _geocode(geocoder, query, kwargs={}, skip_timeouts=True):
    '''
    Pickle-able geocoding method that works with any object that implements a
    "geocode" method
    '''
    method = getattr(geocoder, 'geocode', False)
    assert method and callable(method)
    results = []
    try:
        result = method(query, **kwargs)
    except geopy.exc.GeocoderTimedOut as timeout:
        if not skip_timeouts:
            raise timeout
        else:
            return results
    if not result:
        return results
    for res in result:
        if not res:
            continue
        results.append(res)
    return results

# TODO is it possible to use/inherit a geopy class?
class Geocoder(object):
    def __init__(self, geocoder_name, config):
        self._class = geopy.get_geocoder_for_service(geocoder_name)
        self.geocode_kwargs = config.pop(
            'geocode') if config.get('geocode', None) else {}
        self.reverse_kwargs = config.pop(
            'reverse') if config.get('reverse', None) else {}
        self.geocoder = self._class(**config)
        self.name = geocoder_name

class Location(object):
    def __init__(self, locations):
        '''
        Contains an array of parsed geocoder responses, each of which are
        geopy.Location objects.
        '''
        if not locations:
            return None
        self._locations = locations

    def __unicode__(self):
        return '\n'.join(self.addresses)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return '\n'.join([repr(l) for l in self.locations])

    def __getitem__(self, index):
        return self.locations[index]

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
        return len(self.locations)

    def _polygonisable(self):
        if not self.locations or len(self.locations) <= 1:
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
    def multipoint(self):
        '''
        Returns a shapely.geometry.MultiPoint of the Location
        '''
        if not self.points:
            return None
        return MultiPoint(self._shapely_points())

    @property
    def mbc(self):
        '''
        Returns a shapely.geometry.Polygon representing the minimum bounding
        circle of the candidate locations
        '''
        if not self.points:
            return None
        return utils.minimum_bounding_circle(
            [p[0:2] for p in self._tuple_points()]
        )

    @property
    def concave_hull(self, alpha=0.15):
        '''
        Returns a concave hull of the Location
        '''
        # TODO document return value
        if not self._polygonisable():
            return None
        return utils.concave_hull(
            [p[0:2] for p in self._tuple_points()], alpha
        )

    @property
    def convex_hull(self):
        '''
        Returns a convex hull of the Location
        '''
        # TODO document return value
        if not self._polygonisable():
            return None
        return utils.convex_hull(self._tuple_points())

    @property
    def clusters(self):
        '''
        Returns clusters that have been identified in the Location's candidate
        addresses
        '''
        # TODO document and maybe sub-class the return value
        if not self.points:
            return None
        return utils.get_clusters(self._tuple_points())

class GeocoderPool(object):
    def __init__(self, config=None, geocoders=None):
        '''
        A "pool" of geopy.geocoders, created using a configuration
        '''
        self._config = config
        self._geocoders = DEFAULT_GEOCODER_POOL
        if config:
            if not isinstance(config, dict):
                raise TypeError(
                    "GeocoderPool configuration must be a dictionary"
                )
            self._geocoders = [
                Geocoder(gc, self.config[gc]) for gc in self.config
            ]
        elif geocoders:
            if not isinstance(geocoders, collections.Iterable):
                raise TypeError(
                    "GeocoderPool member geocoders must be an iterable set"
                )
            if not all(isinstance(g, geopy.Geocoder) for f in geocoders):
                raise TypeError(
                    "GeocoderPool member geocoders must be geopy.geocoder geocoder"
                )
            self._geocoders = geocoders


    def __check_duplicates(self):
        '''
        Checks for duplicate members of the geocoding pool. If any are found,
        a warning is emitted and duplicates are removed, leaving only unique
        geocoders.
        '''
        if not len(set(self._geocoders)) == len(self._geocoders):
            warnings.warn(
                "Not all supplied geocoders are unique; ignoring duplicate entries"
            )
            self._geocoders = set(self._geocoders)
        return self._geocoders

    @classmethod
    def fromfile(cls, config, caller=None):
        if not caller:
            with open(config, 'r') as cfg:
                return cls(config=cfg)
        else:
            with open(config, 'r') as cfg:
                return cls(config=caller(cfg))

    @property
    def config(self):
        return self._config

    def geocode(self, query):
        pool = ThreadPool()
        results = pool.starmap(
            _geocode,
            zip(
                [g.geocoder for g in self.geocoders],
                repeat(query),
                [g.geocode_kwargs for g in self.geocoders]
            )
        )
        pool.close()
        pool.join()
        locations = [item for sublist in results for item in sublist]
        return Location(locations)

    @property
    def geocoders(self):
        return self.__check_duplicates()


if __name__ == '__main__':
    import yaml
    config = os.path.abspath(os.path.join(
        os.path.dirname( __file__ ), '..', 'configuration.yml'
    ))
    g_pool = GeocoderPool.fromfile(config, yaml.load)
    test = '66 Great North Road, Grey Lynn, Auckland, 1021, New Zealand'
    location = g_pool.geocode(test)
    print(location)
    print(location.convex_hull.wkt)
    print(location.concave_hull.wkt)
    print(location.multipoint.wkt)
    print(location.clusters)
