"""Orders processing"""

import json
import logging

from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..models.item import Item, ShippingInfo
from ..models.order import Order
# from ..utils import ndb_json
from ..utils.shipping.amazon import AmazonShippingInfo


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
                    item['total_cost'] = item['price'] * item['quantity']
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

    # if items not from amazon
    else:
        def return_item_with_costs(item):
            item['total_cost'] = item['price'] * item['quantity']
            item['shipping_cost'] = item['quantity'] * (2.20462 * 7.50)
            return item
        new_order['items'] = map(return_item_with_costs, new_order['items'])

    # DataStore uses id to retrieve the item auto-assigned key
    # Thus use 'item_id' instead
    def set_item_id(item):
        item['item_id'] = item['id']
        item.pop('id', None)
        return item
    new_order['items'] = map(set_item_id, new_order['items'])

    # calculate the order's total shipping cost
    item_shipping_costs = [item['shipping_cost'] for item in new_order['items']]
    new_order['shipping_cost'] = reduce(lambda a, b: a + b, item_shipping_costs, 0.00)

    # calculate the order's total item costs
    cost_per_items = [item['total_cost'] for item in new_order['items']]
    new_order['total_cost'] = reduce(lambda a, b: a + b, cost_per_items, 0.00)

    # store the items 1st, collecting their DB keys
    items = [Item(**item) for item in new_order['items']]
    item_keys = ndb.put_multi(items)

    # now store the order, referencing the keys to the items of order
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


@orders.route('/order/<string:order_id>/item/<string:item_id>', methods=['DELETE'])
def remove_item_from_order(order_id, item_id):
    pass

@orders.route('/order/<string:order_id>/coupon/<string:coupon_code>', methods=['PUT'])
def apply_coupon_code_to_order(order_id, coupon_code):
    pass
