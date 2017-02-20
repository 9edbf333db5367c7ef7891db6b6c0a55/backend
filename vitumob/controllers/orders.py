"""Orders processing"""

import json
from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..models.order import Order
from ..models.item import Item
from ..utils import ndb_json


orders = Blueprint('orders', __name__)


@orders.route('/orders/new', methods=['POST'])
def new_order_from_user():
    """Receives new orders and stores them"""
    new_order = json.loads(request.json['order'])

    items = [Item(**item) for item in new_order['items']]
    order = Order(name=new_order['name'], host=new_order['host'], items=items)
    order_id = order.put()

    results = Order.query(Order.key == order_id).get()
    payload = json.dumps({'results': ndb_json.dumps(results)})
    return Response(payload, status=200, mimetype='application/json')
