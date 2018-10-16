import os
from flask import Flask, session
from flask_cors import CORS, cross_origin

from .controllers.user import user
from .controllers.orders import orders
from .controllers.cart import cart
from .controllers.payments import payments
from .controllers.mpesa import mpesa
from .controllers.rates import exchangerates
from .controllers.coupons import coupons


app = Flask(__name__)
app.secret_key = os.urandom(18)
CORS(app)

resources = [user, orders, cart, payments, mpesa, exchangerates, coupons]
for resource in resources:
    app.register_blueprint(resource)
