"""Orders processing"""

import json
from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..models.order import Order
from ..models.item import Item
from ..utils import ndb_json


orders = Blueprint('orders', __name__)


@orders.route('/order/new', methods=['POST'])
def new_order_from_extension():
    """Receives a new order and store it"""
    new_order = json.loads(request.json['order'])

    # store the items 1st, collecting their DB keys
    items = [Item(**item) for item in new_order['items']]
    item_keys = [item.put() for item in items]

    # now store the order, referencing the keys to the items of order
    order = Order(name=new_order['name'], host=new_order['host'], items=item_keys)
    order_key = order.put()

    # results = Order.query(Order.key == order_key).get()
    payload = json.dumps({})
    return Response(payload, status=200, mimetype='application/json')
