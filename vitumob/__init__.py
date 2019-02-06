import os
from flask import Flask, session
from flask_cors import CORS, cross_origin

from .controllers.user import user
from .controllers.orders import orders
from .controllers.cart import cart
from .controllers.paypal import paypal_payments
from .controllers.mpesa_ipn import mpesa_ipn
from .controllers.rates import exchangerates
# from .controllers.coupons import coupons
from .controllers.mpesa_push_api import mpesa_push_api
from .controllers.surchage_api import shipping_info


app = Flask(__name__)
app.secret_key = os.urandom(18)
CORS(app)

resources = [user, orders, cart, exchangerates, paypal_payments, mpesa_ipn, mpesa_push_api, shipping_info]
for resource in resources:
    app.register_blueprint(resource)
