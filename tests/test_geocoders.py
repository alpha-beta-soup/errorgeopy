import os
import encodings.idna

import pytest
import yaml
import geopy
import shapely

import errorgeopy.geocoders
'''
import yaml
config = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'configuration.yml'))
g_pool = GeocoderPool.fromfile(config, yaml.load)
test = '66 Great North Road, Grey Lynn, Auckland, 1021, New Zealand'
location = g_pool.geocode(test)
if location:
    print(location)
    print(location.convex_hull.wkt)
    print(location.concave_hull.wkt)
    print(location.multipoint.wkt)
    c = location.clusters
    for cl in c:
        if not cl['centre'] or not cl['members']: continue
        print('CENTRE: %s' % cl['centre'].wkt,
              'MEMBERS: %s' % cl['members'].wkt)

    test = location[0]
    address = g_pool.reverse((test.latitude, test.longitude))
    print(address.dedupe())
    print(address.longest_common_substring())
    print(address.extract('Great North Grey Lynn 1021'))
'''


@pytest.fixture
def addresses():
    return (
        '66 Great North Road, Grey Lynn, Auckland, 1021, New Zealand',
        'High Street, Lower Hutt, New Zealand',
        '10 Aurora Street, Petone, Lower Hutt, Wellington',  # Doesn't produce enough for a cluster
        '10 Aurora Street, Petone, Lower Hutt, 5012',  # Doesn't produce enough for a cluster
        'Oriental Street, Lower Hutt, New Zealand',
        'Oriental Bay, Wellington, New Zealand',
        'Oriental Vay, Wellington, NZ',  # Deliberate typo "Vay",
        'ZJ6AZ2Ixgp1or4O'  # Deliberate nonsense, random string
    )


@pytest.fixture
def addresses_reverse():
    return ((-37.8007774, 174.869645),  # 66 Great North Road
            (-41.2296258, 174.8828724),  # 10 Aurora Street, Petone, Lower Hutt
            (-41.1945832, 174.9403476),  # High Street, Lower Hutt
            (-41.2910862, 174.7882479),  # Oriental Bay, Wellington
            # (-90, 0)  # South Pole
            # (-91, 181)  # Out of range
            )


@pytest.fixture
def configfile():
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'config.yml')


@pytest.fixture
def load_configfile():
    return yaml.load(open(configfile(), 'r'))


@pytest.fixture
def geocoderpool_fromfile():
    return errorgeopy.geocoders.GeocoderPool.fromfile(configfile(), yaml.load)


@pytest.fixture
def geocoderpool():
    return errorgeopy.geocoders.GeocoderPool(load_configfile())


def test_load_gpool_from_file_with_caller():
    gpool = geocoderpool_fromfile()
    assert isinstance(
        gpool, errorgeopy.geocoders.
        GeocoderPool), 'failed to produce a GeocoderPool object on instantiation'
    assert gpool.config == yaml.load(open(configfile(
    ), 'r')), 'configuration was mutated on instantiation'
    assert getattr(gpool._geocoders, '__iter__',
                   False), 'GeocoderPool._geocoders is not iterable'
    assert all([
        issubclass(x.geocoder.__class__, geopy.geocoders.base.Geocoder)
        for x in gpool.geocoders
    ]), 'not all of the GeocoderPool geocoders are geopy.Geocoder objects'


def test_load_gpool_from_file_without_caller():
    gpool = geocoderpool()
    assert isinstance(
        gpool, errorgeopy.geocoders.
        GeocoderPool), 'failed to produce a GeocoderPool object on instantiation'
    assert gpool.config == load_configfile(
    ), 'configuration was mutated on instantiation'
    assert getattr(gpool._geocoders, '__iter__',
                   False), 'GeocoderPool._geocoders is not iterable'
    assert all([
        issubclass(x.geocoder.__class__, geopy.geocoders.base.Geocoder)
        for x in gpool.geocoders
    ]), 'not all of the GeocoderPool geocoders are geopy.Geocoder objects'


def test_geocoder_pool():
    gpool = geocoderpool()
    assert isinstance(gpool.geocoders, list)


def test_geocode():
    gpool = geocoderpool()
    assert callable(gpool.geocode)
    for test_case in addresses():
        res = gpool.geocode(test_case)
        assert isinstance(res, errorgeopy.location.Location)
        assert isinstance(res._polygonisable(), bool)
        assert all(
            [isinstance(x, geopy.location.Location) for x in res.locations])
        assert all([isinstance(x, str) for x in res.addresses])
        assert all([isinstance(x, geopy.Point) for x in res.points])
        assert isinstance(res.multipoint, shapely.geometry.MultiPoint)
        assert isinstance(res.mbc, shapely.geometry.Polygon) or res.mbc is None
        assert isinstance(res.concave_hull, shapely.geometry.Polygon) or (
            res.concave_hull is None and len(res) < 4)
        assert isinstance(res.convex_hull, shapely.geometry.Polygon) or (
            res.convex_hull is None and len(res) < 3)
        assert isinstance(res.centroid, shapely.geometry.Point)
        assert isinstance(res.clusters, errorgeopy.location.LocationClusters)
        assert isinstance(res.clusters.geometry_collection(),
                          shapely.geometry.GeometryCollection)


def test_reverse_geocode():
    gpool = geocoderpool()
    assert callable(gpool.reverse)
    for test_case in addresses_reverse():

        res = gpool.reverse(test_case)

        assert isinstance(res, errorgeopy.address.Address)

        assert len(res.addresses) <= len(res.dedupe())

        assert isinstance(res.longest_common_substring(), str)

        extract1 = res.extract(' '.join(str(res.addresses[0]).split()[::3]))
        assert isinstance(extract1, list)
        if len(extract1) > 0:
            assert type(extract1[0][0]) is geopy.location.Location
            assert type(extract1[0][1]) is int
            assert sorted([e[1] for e in extract1],
                          reverse=True) == [e[1] for e in extract1]

        extract2 = res.extract(res.extract(str(res.addresses[0])[::6]))
        assert isinstance(extract2, list)
        if len(extract2) > 0:
            assert type(extract2[0][0]) is geopy.location.Location
            assert type(extract2[0][1]) is int
            assert sorted([e[1] for e in extract2],
                          reverse=True) == [e[1] for e in extract2]

        with pytest.raises(NotImplementedError):
            res.longest_common_sequence()

        with pytest.raises(NotImplementedError):
            res.regex()

        with pytest.raises(NotImplementedError):
            res.parse()

        with pytest.raises(NotImplementedError):
            res.tag()
