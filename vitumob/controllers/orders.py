"""Orders processing"""

import json
from flask import Blueprint, Response, request
from ..models.order import Order
from ..models.item import Item
# from google.cloud import datastore

orders = Blueprint('orders', __name__)
# entity = datastore.Client()

@orders.route('/orders/new', methods=['POST'])
def new_order_from_user():
    """Receives new orders and stores them"""
    new_order = json.loads(request.json['order'])

    items = [Item(**item) for item in new_order['items']]
    order = Order(name=new_order['name'], host=new_order['host'], items=items)
    order.put()

    payload = json.dumps({'status': 200})
    return Response(payload, status=200, mimetype='application/json')
