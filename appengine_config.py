"""
`appengine_config.py` is automatically loaded when Google App Engine
starts a new instance of your application. This runs before any
WSGI applications specified in app.yaml are loaded.
"""

import os
from google.appengine.ext import vendor

# Add any libraries install in the "vendor" folder.
vendor.add(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib'))