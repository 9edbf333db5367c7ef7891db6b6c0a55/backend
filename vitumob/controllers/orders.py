"""Orders processing"""

import json
import logging
from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..models.order import Order
from ..models.item import Item, ShippingInfo
from ..utils import ndb_json
from ..utils.shipping.amazon import AmazonShippingCost


orders = Blueprint('orders', __name__)


@orders.route('/order/new', methods=['POST'])
def new_order_from_extension():
    """Receives a new order and store it"""
    new_order = json.loads(request.json['order'])

    # if order is from amazon, get the shipping information of each item
    if 'amazon' in new_order['merchant']:
        amazon = AmazonShippingCost(new_order['items'])
        items_shipping_info = amazon.get_shipping_info()

        if len(items_shipping_info) > 0:
            for index, item in enumerate(new_order['items']):
                shipping_info = [info for info in items_shipping_info
                                 if 'asin' in info and info['asin'] == item['id']]

                if len(shipping_info) > 0:
                    shipping_info = shipping_info[0]
                    item['name'] = shipping_info['title']
                    item['total_cost'] = item['price'] + \
                        shipping_info['shipping_cost']

                    shipping_info.pop('asin', None)
                    shipping_info.pop('title', None)
                    item['shipping_info'] = ShippingInfo(**shipping_info)
                else:
                    logging.debug("No shipping information was captured for %s", item['name'])

                new_order['items'][index] = item

    # store the items 1st, collecting their DB keys
    items = [Item(**item) for item in new_order['items']]
    item_keys = [item.put() for item in items]

    # now store the order, referencing the keys to the items of order
    order = Order(merchant=new_order['merchant'], uuid=new_order['uuid'], items=item_keys)
    order_key = order.put() # Order.query(Order.key == order_key).get()

    payload = json.dumps({'orderId': order_key.urlsafe() })
    return Response(payload, status=200, mimetype='application/json')
