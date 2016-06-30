import os

import yaml
from flask import Flask, Response, request
app = Flask(__name__)

from errorgeopy.geocoders import GeocoderPool

@app.route('/', methods=['GET'])
def ErrorGeocode():
    #?address=some-address
    config = os.path.abspath(os.path.join(
        os.path.dirname( __file__ ), '..', 'configuration.yml'
    ))
    address = request.args.get('address')
    g_pool = GeocoderPool.fromfile(config, yaml.load)
    location = g_pool.geocode(address)
    return Response(
        location.multipoint.wkt, 200, mimetype='text/plain'
        # str(location.mbc), 200, mimetype='text/plain'
    )

if __name__ == "__main__":
    app.run()
