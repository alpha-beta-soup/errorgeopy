import os
import collections
import warnings
from multiprocessing.dummy import Pool as ThreadPool
from itertools import repeat
from collections import OrderedDict
import copy

import geopy

from errorgeopy.address import Address
from errorgeopy.location import Location
from errorgeopy import utils, DEFAULT_GEOCODER_POOL


def _action(geocoder, query, method, kwargs={}, skip_timeouts=True):
    '''
    :param geocoder: A geocoder to run a query against.
    :type geocoder: :class: geopy.geocoders.base.Geocoder

    :param query: The address (forward) or location (reverse) you wish to
        geocode.

    :param string method: The name of the method to call on the geocoder (e.g.
        `reverse`, `geocode`).

    :params dict kwargs: Keyword arguments for the method.

    :param bool skip_timeouts: If a timeout is encountered, controls whether the
        normal exception is raised, or if it should be silently ignored.
    '''
    method = getattr(geocoder, method, False)
    assert method and callable(method)
    results = []
    try:
        result = method(query, **kwargs)
    except geopy.exc.GeocoderTimedOut as timeout:
        if not skip_timeouts:
            raise timeout
        else:
            return results
    except NotImplementedError:
        return results
    if not result:
        return results
    results.extend(result if isinstance(result, list) else [result])
    return results


def _geocode(geocoder, query, kwargs={}, skip_timeouts=True):
    '''
    Pickle-able geocoding method that works with any object that implements a
    "geocode" method. Given an address, find locations.

    :param geocoder: A geocoder to run a query against.
    :type geocoder: :class: geopy.geocoders.base.Geocoder

    :param string query: The address you wish to geocode.

    :params dict kwargs: Keyword arguments for the method.

    :param bool skip_timeouts: If a timeout is encountered, controls whether the
        normal exception is raised, or if it should be silently ignored.
    '''
    return _action(geocoder, query, 'geocode', kwargs, skip_timeouts)


def _reverse(geocoder, query, kwargs={}, skip_timeouts=True):
    '''
    Pickle-able reverse geocoding method that works with any object that
    implements a "reverse" method. Given a point, find addresses.

    :param geocoder: A geocoder to run a query against.
    :type geocoder: :class: geopy.geocoders.base.Geocoder

    :param query: The coordinates for which you wish to obtain human-readable
        addresses.
    :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
        longitude), or string as "%(latitude)s, %(longitude)s"

    :params dict kwargs: Keyword arguments for the method.

    :param bool skip_timeouts: If a timeout is encountered, controls whether the
        normal exception is raised, or if it should be silently ignored.
    '''
    return _action(geocoder, query, 'reverse', kwargs, skip_timeouts)


# TODO is it possible to use/inherit a geopy class and extend on the fly?
class Geocoder(object):
    def __init__(self, geocoder_name, config):
        self._class = geopy.get_geocoder_for_service(geocoder_name)
        self.geocode_kwargs = config.pop('geocode') if config.get('geocode',
                                                                  None) else {}
        self.reverse_kwargs = config.pop('reverse') if config.get('reverse',
                                                                  None) else {}
        self.geocoder = self._class(**config)
        self.name = geocoder_name


class GeocoderPool(object):
    def __init__(self, config=None, geocoders=None):
        '''
        A "pool" of geopy.geocoders, created using a configuration
        '''
        self._config = config
        cfg = copy.deepcopy(config)
        self._geocoders = DEFAULT_GEOCODER_POOL
        if config:
            if not isinstance(config, dict):
                raise TypeError(
                    "GeocoderPool configuration must be a dictionary")
            self._geocoders = [Geocoder(gc, cfg[gc]) for gc in cfg]
        elif geocoders:
            if not isinstance(geocoders, collections.Iterable):
                raise TypeError(
                    "GeocoderPool member geocoders must be an iterable set")
            if not all(isinstance(g, geopy.Geocoder) for f in geocoders):
                raise TypeError(
                    "GeocoderPool member geocoders must be geopy.geocoder geocoder")
            self._geocoders = geocoders

    def __unicode__(self):
        return '\n'.join([g.name for g in self._geocoders])

    def __str__(self):
        return self.__unicode__()

    def __check_duplicates(self):
        '''
        Checks for duplicate members of the geocoding pool. If any are found,
        a warning is emitted and duplicates are removed, leaving only unique
        geocoders.
        '''
        if not len(set(self._geocoders)) == len(self._geocoders):
            warnings.warn(
                "Not all supplied geocoders are unique; ignoring duplicate entries")
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

    def _pool_query(self, query, func, attr, callback):
        pool = ThreadPool()
        results = pool.starmap(func, zip([g.geocoder for g in self.geocoders],
                                         repeat(query),
                                         [getattr(g, attr)
                                          for g in self.geocoders]))
        pool.close()
        pool.join()
        locations = []
        for location in results:
            if isinstance(location, list):
                locations.extend(location)
            else:
                locations.append(location)
        # locations = [item for sublist in results for item in sublist]
        return callback(locations)

    def geocode(self, query):
        return self._pool_query(query, _geocode, 'geocode_kwargs', Location)

    def reverse(self, query):
        '''
        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"
        '''
        return self._pool_query(query, _reverse, 'reverse_kwargs', Address)

    @property
    def geocoders(self):
        return self.__check_duplicates()
