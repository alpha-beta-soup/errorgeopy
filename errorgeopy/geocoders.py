"""Contains the `Geocoder` and `GeocoderPool` classes, representing one, and a
pool of pre-configured geocoders, respectively.

`Geocoder` is a very thin piece
of wrapping over `geopy.geocoders.base.Geocoder` that primarily just initialises
a `geopy.Geocoder` instance by referring to it by name and passing
configuration.

`GeocoderPool` coordinates reading of configuration (file or dictionary) of a
suite of geocoders that you should configure, although a small number are
available with no configuration. The `GeoCoder` pool then coordinates requests
via individual `Geocoder` objects, handling failures and geocoding in parallel
for the sake of efficiency. Both forward and backward ("reverse") geocoding is
supported, but note that not all geocoding services exposed via `errorgeopy`
support both methods.

.. moduleauthor Richard Law <richard.m.law@gmail.com>
"""

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
    """Private function, performs a geocoding action.

    Args:
        geocoder (geopy.geocoders.base.Geocoder): A geocoder to run a query
            against.
        query (str, tuple): The address (forward) or location (reverse) you
            wish to geocode.
        method (str): The name of the method to call on the geocoder (e.g.
            "reverse", "geocode").

    Kwargs:
        kwargs (dict): Kwargs for the method.
        skip_timeouts (bool): If a timeout is encountered, controls whether the
            normal exception is raised, or if it should be silently ignored.
    """
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
    """Pickle-able geocoding method that works with any object that implements a
    "geocode" method. Given an address, find locations.

    Notes:
        See :code:`_action` function; this just supplies the :code:`method` to
        that function (as "geocode"). Therefore geocoder must have a callable
        method called "geocode".
    """
    return _action(geocoder, query, 'geocode', kwargs, skip_timeouts)


def _reverse(geocoder, query, kwargs={}, skip_timeouts=True):
    """Pickle-able reverse geocoding method that works with any object that
    implements a "reverse" method. Given a point, find addresses.

    Notes:
        See :code:`_action` function; this just supplies the :code:`method` to
        that function (as "reverse"). Therefore geocoder must have a callable
        method called "reverse".

    Kwargs:
        query (:class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s")
    """
    return _action(geocoder, query, 'reverse', kwargs, skip_timeouts)


# TODO is it possible to use/inherit a geopy class and extend on the fly?
class Geocoder(object):
    """A single geocoder exposing access to a geocoding web service with geopy.
    Thin wrapping over the geopy.Geocoder set of geocoding services.
    Used by `errorgeopy.GeocoderPool` to access the configuration of each
    component service. The base `geopy.Geocoder` object can be obtained via the
    `geocoder` attribute.
    """

    def __init__(self, name, config):
        """A single geocoding service with configuration.

        Args:
            name (str): Name of the geocoding service. Must be a name used by
                geopy.
            config (dict): Configuration for that geocoder, meeting the geopy
                API.
        """
        self._name = name
        self._geocode_kwargs = config.pop('geocode') if config.get(
            'geocode', None) else {}
        self._reverse_kwargs = config.pop('reverse') if config.get(
            'reverse', None) else {}
        self._config = config

    @property
    def geocoder(self):
        """The `geopy.Geocoder` instance.
        """
        return geopy.get_geocoder_for_service(self.name)(**self._config)

    @property
    def name(self):
        """The  string name of the geocoder.
        """
        return self._name

    @property
    def config(self):
        """The configuration of the geocoder (less the kwargs for the `geocode`
        and `reverse` methods), as a dictionary.
        """
        return self._config


class GeocoderPool(object):
    """A "pool" of objects that inherit from
    :code:`geopy.geocoders.base.Geocoder`, with configuration specific to each
    service. Represents the inputs for geocoding operations that span across
    multiple providers. Queries are run in parallel across all configured
    geocoding providers, and results are intended to be a composition of
    multiple responses from different providers with coherent configuration
    (e.g. a universal :code:`country_bias`), although this is not enforced.
    """

    def __init__(self, config=None, geocoders=None):
        """Initialises a pool of geocoders to run queries over in parallel.

        Args:
            config (dict): A dictionary representing configuration for a suite
                of geocoders to be used for geocoding queries.
            geocoders: An iterable array of geopy.Geocoder objects that will be
                used for geocoding. The `config` options will be used to provide
                arguments to the `geocode` and `reverse` methods.

        Notes:
            The structure of the configuration file (GeocoderPool.fromfile) or
            dictionary (GeocoderPool.__init__) must match the names of geopy
            geocoders, their instantiation options, and method signatures for
            `geocode` and `reverse`. See the `geopy documentation`_ for possible
            options. Note in particular that for a large number of possible
            geocoders, authentication tokens are required. They must be included
            in your configuration; so be careful with including this file in
            source control or generally sharing it. The default arguments used
            by geopy will be used if any keyword arguments are absent in the configuration.

        .. _`geopy documentation`: http://geopy.readthedocs.io/en/latest/
        """
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

    @property
    def config(self):
        """The (parsed) configuration that will be referred to
        when geocoding, as a dictionary.
        """
        return self._config

    @property
    def geocoders(self):
        """The list of unique geocoders that will be used when geocoding. Each
        member of the array inherits from `geopy.geocoder.base`.
        """
        return self._check_duplicates()

    def _check_duplicates(self):
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
        """Instantiates a GeocoderPool from a configuration file. For example,
        a `config.yml` file may look like::

            ArcGIS:
              geocode:
                exactly_one: true
              reverse:
                distance: 1000
            Nominatim:
              country_bias: "New Zealand"
              geocode:
                addressdetails: true
                language: en
                exactly_one: false
              reverse:
                exactly_one: true
                language: en

        Then you could use this classmethod as follows:

            >>> import yaml
            >>> from errorgeopy.geocoders import GeocoderPool
            >>> gpool = GeocoderPool.fromfile('./config.yml', yaml.load)

        Args:
            config (str): path to a configuration file on your system.

        Kwargs:
            caller (function): optional method that will parse the config file
            into a Python dictionary with keys matching GeoPy geocoder names,
            and those keys holding values that are also dictionaries: function
            signatures for `geocode` and `reverse`, and any other
            geocoder-specific configuration (e.g. `country_bias` above).
        """

        if not caller:
            with open(config, 'r') as cfg:
                return cls(config=cfg)
        else:
            with open(config, 'r') as cfg:
                return cls(config=caller(cfg))

    def _pool_query(self, query, func, attr, callback):
        """Uses :code:`query` to perform :code:`func` with kwargs :code:`attr`
        in parallel against all configured geocoders. Performs :code:`callback`
        function on the result list of addresses or locations.

        Args:
            query (str): The query component of a reverse or forward geocode.
                func (function): Function to use to obtain an answer.
            attr (dict): Keyword arguments to pass to function for each
                geocoder.
            callback (func): Function to run over iterable result.

        Returns:
            Output of `callback`.
        """
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
        """Forward geocoding: given a string address, return a point location.
        ErrorGeoPy does this, and also provides you with ways to interrogate the
        spatial error in the result.

        Args:
            query (str): Address you want to find the location of (with spatial
                error).

        Returns:
            A list of `errorgeopy.address.Address` instances.
        """
        return self._pool_query(query, _geocode, '_geocode_kwargs', Location)

    def reverse(self, query):
        """Reverse geocoding: given a point location, returns a string address.
        ErrorGeoPy does this, and also provides you with ways to interrogate the
        uncertainty in the result.

        Args:
            query (`geopy.point.Point`, iterable of (lat, lon), or string as
            "%(latitude)s, %(longitude)s"): The coordinates for which you wish
            to obtain the closest human-readable addresses.

        Returns:
            A list of `errorgeopy.location.Location` instances.
        """
        return self._pool_query(query, _reverse, '_reverse_kwargs', Address)
