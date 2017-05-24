import json
import logging

from flask import Response
from vitumob import app


@app.route('/')
def index_health_check():
    payload = json.dumps({'status': 200, 'message': 'Everything Everyday!'})
    return Response(payload, status=200, mimetype='application/json')


@app.errorhandler(500)
def server_error(error):
    logging.exception('An error occurred during a request.')
    payload = json.dumps({
        'status': 500,
        'error': "{}".format(error),
    })
    return Response(payload, status=500, mimetype='application/json')


if __name__ == '__main__':
    # This is used when running locally.
    app.run(host='127.0.0.1', port=8080, debug=True)
