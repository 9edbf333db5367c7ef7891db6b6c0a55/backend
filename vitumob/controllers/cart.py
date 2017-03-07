from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..utils import ndb_json
from ..models.order import Order

cart = Blueprint('cart', __name__)

@cart.route('/cart/<string:order_id>', methods=['GET'])
def get_order_by_id(order_id):
    order = ndb.Key(Order, ndb.Key(urlsafe=order_id).id())
    order = order.get().to_dict()

    def return_with_key(item):
        """Add missing DB ID(key) to each item in the payload"""
        new_item = item.key.get().to_dict()
        new_item['id'] = item.key.urlsafe()
        new_item['num_id'] = item.key.id()
        return new_item
    order['items'] = map(return_with_key, ndb.get_multi(order['items']))
    order['id'] = order_id

    payload = ndb_json.dumps(order)
    return Response(payload, status=200, mimetype='application/json')
