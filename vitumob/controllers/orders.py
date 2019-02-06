"""Orders processing"""

import os
import json
import time
import calendar
import logging

from functools import reduce
from datetime import datetime
from flask import Blueprint, Response, request
# from google.appengine.api import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from hashids import Hashids

import requests
import requests_toolbelt.adapters.appengine

from ..models.rates import Currency
from ..models.item import Item, ShippingInfo
from ..models.order import Order
from ..models.user import User
from ..models.rates import Rates
# Deprecated
# from ..utils.shipping.amazon import AmazonShippingInfo
from ..utils.shipping.sellers_central_amazon import ItemShippingInfo
from ..utils import ndb_json


orders = Blueprint('orders', __name__)
endpoint = os.environ.get("HOSTGATOR_SYNC_ENDPOINT")
requests_toolbelt.adapters.appengine.monkeypatch()


def store_items_and_create_order(new_order, usd_to_kes):
    # store the items 1st, collecting their assigned reference keys from DB
    items = [Item(**item) for item in new_order['items']]
    item_keys = ndb.put_multi(items)

    # reference the keys to the items in the order and store the order
    new_order['items'] = item_keys

    hashids = Hashids(salt='https://vitumob.com/orders', min_length=8)
    new_order_key = ndb.Key(Order, hashids.encode('VM', str(calendar.timegm(time.gmtime()))))
    order = Order.get_or_insert(new_order_key.id())
    order.populate(**new_order)
    order.put() # Order.query(Order.key == order_key).get()

    return {
        'order_id': order.key.id(),
        'order_hex': order.key.urlsafe(),
        'total_cost': order.total_cost,
        'customs': order.customs,
        'vat': order.vat,
        'overall_cost': order.overall_cost,
        'shipping_cost': order.shipping_cost,
        'markup': order.markup,
        'exchange_rate': usd_to_kes.rate,
    }


@orders.route('/order', methods=['POST'])
def new_order_from_extension():
    """Receives a new order and store it"""
    new_order = json.loads(request.json['order'])

    if os.environ.get("ENV") == "development":
        rates_key = ndb.Key(Rates, os.environ.get('OPENEXCHANGE_API_ID'))
        rates = Rates.get_by_id(rates_key.id())
        usd_to_kes = [rate for rate in rates.rates if rate.code == 'KES'][0]
    else:
        usd_to_kes = Currency(code="KES", rate=105.00)

    # if order is from amazon, get the shipping information of each item
    if 'amazon' in new_order['merchant']:
        amazon_order_items = ItemShippingInfo(new_order['items'])
        response, status_code = amazon_order_items.retrieve_shipping_info()
        # print response

        if len(response) == 0 and status_code != 200:
            return Response(json.dumps({'error': response}), status=504, mimetype='application/json')

        items_with_shipping_info = response
        logging.info(items_with_shipping_info)

        for index, item in enumerate(new_order['items']):
            shipping_info = [shpn_info for shpn_info in items_with_shipping_info
                                if 'asin' in shpn_info and shpn_info['asin'] == item['id']]

            if len(shipping_info) == 0:
                # print "No shipping information was captured for %s" % item['name']
                logging.debug(
                    "No shipping information was captured for %s",
                    item['name']
                )
                new_order['items'][index] = item
                continue

            shipping_info = shipping_info[0]
            shipping_info['local_cost'] = shipping_info['shipping_cost'] * usd_to_kes.rate

            item['name'] = shipping_info['title']
            item['shipping_cost'] = shipping_info['shipping_cost'] * item['quantity']

            shipping_info.pop('asin', None)
            shipping_info.pop('title', None)

            item['shipping_info'] = ShippingInfo(**shipping_info)
            new_order['items'][index] = item

    def update_item_information(item):
        """delete id, calculate total_cost and add missing shipping_cost"""
        # reassign the 'id' property and delete it
        # datastore uses 'id' to retrieve the item auto-assigned key
        item['item_id'] = item['id']
        item.pop('id', None)

        # get the item's price in KES
        item['local_price'] = round(item['price'] * usd_to_kes.rate, 2)

        # get total_cost per item
        item['total_cost'] = item['price'] * item['quantity']

        # if shipping info is missing get the default shipping cost
        if 'shipping_info' not in item:
            item['shipping_cost'] = item['quantity'] * (2.20462 * 7.50)

        return item
    new_order['items'] = map(update_item_information, new_order['items'])
    new_order['exchange_rate'] = usd_to_kes.rate

    # calculate the order's total shipping cost
    item_shipping_costs = [item['shipping_cost'] for item in new_order['items']]
    new_order['shipping_cost'] = reduce(lambda a, b: a + b, item_shipping_costs, 0.00)

    # calculate the order's total item costs
    cost_per_items = [item['total_cost'] for item in new_order['items']]
    new_order['total_cost'] = reduce(lambda a, b: a + b, cost_per_items, 0.00)

    new_order['total_cost'] = round(new_order['total_cost'], 2)
    new_order['shipping_cost'] = round(new_order['shipping_cost'], 2)

    # If the total cost of items is more than $800 shipping cost is completely waved
    if new_order['total_cost'] >= 800:
        new_order['waived_shipping_cost'] = new_order['shipping_cost']
        new_order['shipping_cost'] = 0.00

    new_order['customs'] = round(new_order['total_cost'] * 0.12, 2)
    new_order['vat'] = round(new_order['total_cost'] * 0.16, 2)

    new_order['overall_cost'] = reduce(lambda a, b: a + b, [
        new_order['total_cost'],
        new_order['shipping_cost'],
        new_order['customs'],
        new_order['vat']
    ], 0.00)
    new_order['overall_cost'] = round(new_order['overall_cost'], 2)
    new_order['local_overall_cost'] = new_order['overall_cost'] * new_order['exchange_rate']
    new_order['markup'] = round((new_order['overall_cost'] / new_order['total_cost']) - 1, 2)

    response = new_order
    if 'create_order' in request.json['order']:
        response = store_items_and_create_order(new_order, usd_to_kes)
        payload = json.dumps(response)
        return Response(payload, status=200, mimetype='application/json')

    # remove shipping_info from the item dictionary
    response['items'] = map(lambda item: (item.pop('shipping_info', None) is True) or item, response['items'])

    payload = json.dumps(response)
    return Response(payload, status=200, mimetype='application/json')


def sync_users_order_to_hostgator(endpoint, order_key):
    """Sync this order with user info to Hostgator admin servers"""
    order = order_key.get()
    order_payload = order.to_dict()
    order_payload['id'] = order_key.id()
    order_payload['user_id'] = order.user.get().key.id()
    payload = ndb_json.dumps({
        'order': order_payload,
    })
    logging.info("Payload: {}".format(payload))
    resource = '{endpoint}/order'.format(endpoint=endpoint)
    response = requests.post(resource, data=payload)

    logging.info("Response Status Code: {status_code}, Response Body: {body}".format(
        status_code=response.status_code,
        body=response.text
    ))


@orders.route('/order/<string:order_id>', methods=['PUT', 'PATCH'])
def relate_user_to_their_order(order_id):
    """Adds user to the order they created for relational purposes"""
    order_key = ndb.Key(urlsafe=order_id)
    order = order_key.get()

    if order is not None:
        logging.info("posted-user:{}".format(request.json['user']))
        posted_user = json.loads(request.json['user'])
        user_key = ndb.Key(User, posted_user['id'])
        user = user_key.get()

        if user is not None:
            order.user = user_key
            order.put()

            # task = taskqueue.add(
            #     url='/order/{order_id}'.format(order_id=order_key.id()),
            #     method='GET',
            #     target='worker',
            # )

            deferred.defer(sync_users_order_to_hostgator, endpoint, order_key)

            timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now())
            payload = json.dumps({'timestamp': timestamp})
            return Response(payload, status=200, mimetype='application/json')

        payload = json.dumps({'message': 'error/user-not-found'})
        return Response(payload, status=404, mimetype='application/json')

    payload = json.dumps({'message': 'error/order-not-found'})
    return Response(payload, status=404, mimetype='application/json')


@orders.route('/order/<string:order_id>/payment', methods=['GET'])
def get_order_payment_details(order_id):
    order_key = ndb.Key(urlsafe=order_id)
    order = order_key.get()

    payment = order.paypal_payment.get()
    payload = payment.to_dict()
    payload['id'] = payment.key.id()
    payload['order_id'] = order_key.id()
    payload = ndb_json.dumps(payload)
    return Response(payload, status=200, mimetype='application/json')
