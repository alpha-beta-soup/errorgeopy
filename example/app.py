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
    with open(config, 'r') as geocoders:
        #?address=some-address
        address = request.args.get('address')
        g_pool = GeocoderPool(yaml.load(geocoders))
        location = g_pool.geocode(address)
        return Response(
            location.get_multipoint().wkt, 200, mimetype='text/plain'
        )

if __name__ == "__main__":
    app.run()
