"""Orders processing"""

import json
import logging

from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..models.item import Item, ShippingInfo
from ..models.order import Order
from ..utils.shipping.amazon import AmazonShippingInfo
# from ..utils import ndb_json


orders = Blueprint('orders', __name__)


@orders.route('/order', methods=['POST'])
def new_order_from_extension():
    """Receives a new order and store it"""
    new_order = json.loads(request.json['order'])

    # if order is from amazon, get the shipping information of each item
    if 'amazon' in new_order['merchant']:
        amazon = AmazonShippingInfo(new_order['items'])
        items_shipping_info = amazon.get_shipping_info()

        if len(items_shipping_info) > 0:
            for index, item in enumerate(new_order['items']):
                shipping_info = [info for info in items_shipping_info
                                 if 'asin' in info and info['asin'] == item['id']]

                if len(shipping_info) > 0:
                    shipping_info = shipping_info[0]
                    item['name'] = shipping_info['title']
                    item['shipping_cost'] = shipping_info['shipping_cost'] * item['quantity']

                    shipping_info.pop('asin', None)
                    shipping_info.pop('title', None)
                    item['shipping_info'] = ShippingInfo(**shipping_info)
                else:
                    logging.debug(
                        "No shipping information was captured for %s",
                        item['name']
                    )

                new_order['items'][index] = item

    def run_some_tasks_per_item(item):
        """delete id, calculate total_cost and add missing shipping_cost"""
        # reassign the 'id' property and delete it
        # datastore uses 'id' to retrieve the item auto-assigned key
        item['item_id'] = item['id']
        item.pop('id', None)

        # get total_cost per item
        item['total_cost'] = item['price'] * item['quantity']

        # if shipping info is missing get the default shipping cost
        if 'shipping_info' not in item:
            item['shipping_cost'] = item['quantity'] * (2.20462 * 7.50)

        return item
    new_order['items'] = map(run_some_tasks_per_item, new_order['items'])

    # calculate the order's total shipping cost
    item_shipping_costs = [item['shipping_cost'] for item in new_order['items']]
    new_order['shipping_cost'] = reduce(lambda a, b: a + b, item_shipping_costs, 0.00)

    # calculate the order's total item costs
    cost_per_items = [item['total_cost'] for item in new_order['items']]
    new_order['total_cost'] = reduce(lambda a, b: a + b, cost_per_items, 0.00)

    # store the items 1st, collecting their assigned reference keys from DB
    items = [Item(**item) for item in new_order['items']]
    item_keys = ndb.put_multi(items)

    # reference the keys to the items in the order
    # and store the order
    new_order['items'] = item_keys
    order = Order(**new_order)
    order_key = order.put() # Order.query(Order.key == order_key).get()

    commited_order = order_key.get()
    payload = json.dumps({
        'order_id': order_key.id(),
        'order_hex': order_key.urlsafe(),
        'total_cost': commited_order.total_cost,
        'customs': commited_order.customs,
        'vat': commited_order.vat,
        'overall_cost': commited_order.overall_cost,
        'shipping_cost': commited_order.shipping_cost,
        'markup': commited_order.markup
    })
    return Response(payload, status=200, mimetype='application/json')

