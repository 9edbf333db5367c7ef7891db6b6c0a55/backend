from flask import Flask
from .controllers.orders import orders

app = Flask(__name__)
app.register_blueprint(orders)
