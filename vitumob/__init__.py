from flask import Flask
from flask_cors import CORS, cross_origin

from .controllers.orders import orders
from .controllers.cart import cart
from .controllers.coupons import coupons
from .controllers.rates import exchangerates
from .controllers.payments import payments


app = Flask(__name__)
CORS(app)

resources = [orders, cart, coupons, exchangerates, payments]
for resource in resources:
    app.register_blueprint(resource)
