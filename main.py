import json
import logging

from flask import Response
from vitumob import app

@app.route('/')
def index():
    return Response(
        json.dumps({ 'status': 200, 'message': 'Hello world!' }),
        status=200,
        mimetype='application/json'
    )

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
