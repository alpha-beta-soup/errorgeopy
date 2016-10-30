"""
.. module:: errorgeopy
   :platform: Unix
   :synopsis: Python geocoding in a disagreeing world.

.. moduleauthor:: Richard Law <richard.m.law@gmail.com>
"""

__version__ = '1.0.0'


def _get_default_pool_members():
    from geopy.geocoders import Nominatim, GoogleV3
    return (Nominatim(), GoogleV3())


DEFAULT_GEOCODER_POOL = _get_default_pool_members()
