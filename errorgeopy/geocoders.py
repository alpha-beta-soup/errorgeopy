import os
from multiprocessing.dummy import Pool as ThreadPool
from itertools import repeat

import geopy
from shapely.geometry import MultiPoint

import errorgeopy.utils as utils

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
        assert locations
        if not isinstance(locations, list):
            self.locations = [locations]
        else:
            self.locations = locations
        self.points = self.get_points()

    def _polygonisable(self):
        if not self.locations or len(self.locations) <= 1:
            return False
        return True

    def get_points(self):
        return [(r.longitude, r.latitude,) for r in self.locations]

    def get_multipoint(self):
        if not self.points:
            return None
        return MultiPoint(self.points)

    def get_multipoint(self):
        if not self.points:
            return None
        return MultiPoint(self.points)

    def get_concave_hull(self, alpha=0.15):
        if not self._polygonisable():
            return None
        return utils.concave_hull(self.points, alpha)

    def get_convex_hull(self):
        if not self._polygonisable():
            return None
        return utils.convex_hull(self.points)

    def get_clusters(self):
        if not self.points:
            return None
        return utils.get_clusters(self.location)


class GeocoderPool(object):
    def __init__(self, config):
        self.config = config
        if not isinstance(self.config, dict):
            # TODO GeocoderPool as just an array of configured geopy geocoders
            raise NotImplementedError
        self.geocoders = self.get_geocoders()

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

    def get_geocoders(self):
        return [Geocoder(gc, self.config[gc]) for gc in self.config]


if __name__ == '__main__':
    import yaml
    # TODO work with already-instantiated geopy geocoders, too
    config = os.path.abspath(os.path.join(
        os.path.dirname( __file__ ), '..', 'configuration.yml'
    ))
    with open(config, 'r') as geocoders:
        g_pool = GeocoderPool(yaml.load(geocoders))
        test = '66 Great North Road, Grey Lynn, Auckland, New Zealand'
        location = g_pool.geocode(test)
        print(location.get_convex_hull().wkt)
        print(location.get_concave_hull().wkt)
        print(location.get_multipoint().wkt)
        print(location.get_clusters())
