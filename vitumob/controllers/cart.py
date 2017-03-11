import json

from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..utils import ndb_json
from ..models.order import Order

cart = Blueprint('cart', __name__)


@cart.route('/cart/<string:order_id>', methods=['GET'])
def get_order_by_id(order_id):
    """Return order by ID"""
    order = ndb.Key(Order, ndb.Key(urlsafe=order_id).id())
    order = order.get().to_dict()

    def add_item_id_and_key(item):
        """Add missing DB ID(key) to each item in the payload"""
        new_item = item.key.get().to_dict()
        new_item['id'] = item.key.urlsafe()
        new_item['num_id'] = item.key.id()
        return new_item
    order['items'] = map(add_item_id_and_key, ndb.get_multi(order['items']))
    order['id'] = order_id

    payload = ndb_json.dumps(order)
    return Response(payload, status=200, mimetype='application/json')


@cart.route('/cart/<string:order_id>/item/<string:item_id>', methods=['PUT'])
def update_item_quantity_in_order(order_id, item_id):
    """
    Update the quantity of the item with the user selected one
    or by 1 if user hasnt provided any quantity amount (just pressed the + button)
    """
    order = ndb.Key(Order, ndb.Key(urlsafe=order_id).id())
    order = order.get()
    order_items = ndb.get_multi(order.to_dict()['items'])

    item = [item.key.get() for item in order_items if item.key.urlsafe() == item_id]
    if len(item) > 0:
        item = item[0]
        item.quantity = (request.json['quantity']
                         if request.json and 'quantity' in request.json else item.quantity + 1)
        # update the item in the DB
        item.put()

        # now we also need to update the order information
        # recalculate the order's total shipping cost
        item_shipping_costs = [item.shipping_cost for item in order_items]
        order.shipping_cost = reduce(lambda a, b: a + b, item_shipping_costs, 0.00)

        # recalculate the order's total item costs
        cost_per_items = [item.total_cost for item in order_items]
        order.total_cost = reduce(lambda a, b: a + b, cost_per_items, 0.00)
        order.put()

        payload = ndb_json.dumps(order)
        return Response(payload, status=200, mimetype='application/json')

    # No item was found with the given item_id
    payload = json.dumps({
        'message': 'There is no item in the database that matches the ID %s' % item_id
    })
    return Response(payload, status=404, mimetype='application/json')

