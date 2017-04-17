from flask import Flask
from .controllers.orders import orders
from .controllers.cart import cart
from .controllers.coupons import coupons

app = Flask(__name__)
app.register_blueprint(orders)
app.register_blueprint(cart)
app.register_blueprint(coupons)
