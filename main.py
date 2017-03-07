import json
import logging

from flask import Response
from vitumob import app


@app.route('/')
def index():
    health_check = json.dumps({'status': 200, 'message': 'Hello world!'})
    return Response(health_check, status=200, mimetype='application/json')

@app.errorhandler(500)
def server_error(error):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(error), 500

if __name__ == '__main__':
    # This is used when running locally.
    app.run(host='127.0.0.1', port=8080, debug=True)
