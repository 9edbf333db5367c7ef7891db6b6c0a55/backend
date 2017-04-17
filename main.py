import json
import logging

from flask import Response
from vitumob import app


@app.route('/')
def index_health_check():
    payload = json.dumps({'status': 200, 'message': 'This is a workshop!'})
    return Response(payload, status=200, mimetype='application/json')


# @app.route('/.well-known/acme-challenge/2r6jnEs30BDi_HxILHm0CjHcoPiwShcgj170pUAi00c')
# def text_file():
#     return Response(
#         "2r6jnEs30BDi_HxILHm0CjHcoPiwShcgj170pUAi00c.dlf2j_BIl7PBEmHH0MRMrpiy2320lU4SzFr4iGWJlrI",
#         status=200,
#         mimetype="text/plain"
#     )


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
