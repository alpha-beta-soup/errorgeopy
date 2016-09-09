from geopy.geocoders import Nominatim, GoogleV3

__version__ = '0.0.4'
DEFAULT_GEOCODER_POOL = (Nominatim(), GoogleV3())
