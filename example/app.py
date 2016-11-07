import os
import ast
import json

import yaml
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS, cross_origin
from geopy.exc import GeocoderServiceError

from errorgeopy.geocoders import GeocoderPool

app = Flask(__name__)
CORS(app)

CONFIG = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'configuration.yml'))
GPOOL = GeocoderPool.fromfile(CONFIG, yaml.load)


def get_config(excluding, exactly_one=False):
    config = {
        "nominatim": {
            "geocode": {"exactly_one": exactly_one},
            "reverse": {"exactly_one": exactly_one}
        },
        "GoogleV3": {
            "api_key": "AIzaSyBZKxKxBop73WBKfG9721QoQAyfrdQgAvU",
            "geocode": {"exactly_one": exactly_one},
            "reverse": {"exactly_one": exactly_one}
        },
        "Bing": {
            "api_key":
            "AkDz9CJ6Chj2nFo67bx9RoaQt0-HSKeXwbFkFb_Dm5ppJQxZL4fAlKfyM81fWreH",
            "geocode": {"exactly_one": exactly_one},
            "reverse": {"exactly_one": exactly_one}
        },
        "GeoNames": {
            "username": "alphabetasoup",
            "geocode": {"exactly_one": exactly_one}
        },
        "LiveAddress": {
            "auth_id": "d2c85338-6385-f5a4-e0b9-c4f5881e9207",
            "auth_token": "z2lNW6tJPQGLsSwNHb60",
            "candidates": 10,
            "geocode": {"exactly_one": exactly_one}
        },
        "OpenCage": {
            "api_key": "c2a3f1a4e0b4880d9e848c0ccea8c7e7",
            "geocode": {"exactly_one": exactly_one},
            "reverse": {"exactly_one": exactly_one}
        },
        "ArcGIS": {
            "geocode": {"exactly_one": exactly_one}
        }
    }
    return {k: v for k, v in config.items() if k not in excluding}


def get_geocoding_pool(config):
    return GeocoderPool(config, yaml.load)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def location_summary(location):
    fc = {"type": "FeatureCollection", "features": []}

    append = lambda geom, properties: fc["features"].append({"type": "Feature", "geometry": geom, "properties": properties})
    if location.multipoint:
        append(location.multipoint.__geo_interface__, {"label": "multipoint"})
    if location.mbc:
        append(location.mbc.__geo_interface__,
               {"label": "minimum bounding circle"})
    if location.concave_hull:
        append(location.concave_hull.__geo_interface__,
               {"label": "concave hull"})
    if location.convex_hull:
        append(location.convex_hull.__geo_interface__,
               {"label": "convex hull"})
    if location.most_central_location:
        append(location.most_central_location.__geo_interface__,
               {"label": "centre"})
    return fc


def location_cluster_summary(location):
    fc = {"type": "FeatureCollection", "features": []}
    append = lambda geom, properties: fc["features"].append({"type": "Feature", "geometry": geom, "properties": properties})
    for rank, loc in enumerate(location.clusters, 1):
        append(loc.location.most_central_location.__geo_interface__,
               {'label': 'representative point',
                'rank': rank})
        if loc.location.multipoint:
            append(loc.location.multipoint.__geo_interface__,
                   {'label': 'multipoint'})
        if (not loc.location.mbc.is_empty) and (
                loc.location.convex_hull is not None):
            append(loc.location.convex_hull.__geo_interface__, {'label':
                                                                'convex hull',
                                                                'rank': rank})
    print(fc)
    return fc


def reverse_summary(address):
    return {
        "addresses": [str(a) for a in address.addresses],
        "de-duplicated addresses": list(address.dedupe()),
        "longest common substring": address.longest_common_substring(),
        "longest common substring (de-deuplicated)":
        address.longest_common_substring(dedupe=True)
    }


@app.route('/forward', methods=['GET'])
def forward(exactly_one=False):
    #?address=some-address
    address = request.args.get('address')
    excluding = request.args.getlist('excluding')
    exactly_one = bool(int(request.args.get('one', exactly_one)))
    gpool = get_geocoding_pool(get_config(excluding, exactly_one))
    if not address:
        raise InvalidUsage('address parameter must be specified',
                           status_code=400)
    location = gpool.geocode(address)
    return jsonify(location_summary(location))


@app.route('/forward/cluster', methods=['GET'])
def forward_cluster(exactly_one=False):
    #?address=some-address&excluding=Googlev3&excluding=ArcGIS&one=1
    address = request.args.get('address')
    excluding = request.args.getlist('excluding')
    exactly_one = bool(int(request.args.get('one', exactly_one)))
    gpool = get_geocoding_pool(get_config(excluding, exactly_one))
    if not address:
        raise InvalidUsage('address parameter must be specified',
                           status_code=400)
    location = gpool.geocode(address)
    return jsonify(location_cluster_summary(location))


@app.route('/reverse', methods=['GET'])
def reverse(exactly_one=False):
    #?lat=float&lon=float
    lat, lon = request.args.get('lat'), request.args.get('lon')
    excluding = request.args.getlist('excluding')
    exactly_one = bool(int(request.args.get('one', exactly_one)))
    gpool = get_geocoding_pool(get_config(excluding))
    if None in (lat, lon):
        raise InvalidUsage('lat and lon parameters must be specified',
                           status_code=400)
    try:
        address = gpool.reverse((float(lat), float(lon)))
    except GeocoderServiceError as exc:
        error = ast.literal_eval(exc.__str__())
        status = error.pop('code')
        error['message'] += ' ' + '. '.join(error.pop('details'))
        raise InvalidUsage(error['message'], status_code=status)

    return jsonify(reverse_summary(address))


if __name__ == "__main__":
    app.run()
