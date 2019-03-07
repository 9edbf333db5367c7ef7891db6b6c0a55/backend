
import os
import json
import logging

from functools import reduce
from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..models.rates import Currency
from ..models.rates import Rates
from ..utils.shipping.sellers_central_amazon import ItemShippingInfo

shipping_info = Blueprint('shipping_info', __name__)

@shipping_info.route('/shipping_info', methods=['GET', 'POST'])
def get_items_shipping_costs():
    user_order = request.json['order']

    if os.environ.get("ENV") is not "development":
        rates_key = ndb.Key(Rates, os.environ.get('OPENEXCHANGE_API_ID'))
        rates = Rates.get_by_id(rates_key.id())
        usd_to_kes = [rate for rate in rates.rates if rate.code == 'KES'][0]
    else:
        usd_to_kes = Currency(code="KES", rate=102.00)

    amazon_items = ItemShippingInfo(user_order['items'])
    response, status_code = amazon_items.retrieve_shipping_info()
    # print(response, status_code)

    if status_code not in [200, 201]:
        payload = json.dumps({'error': response})
        return Response(payload, status=status_code, mimetype='application/json')

    shipping_info_of_items = response
    # logging.debug(shipping_info_of_items)
    def add_shipping_info_to_item(item):
        item_shipping_info = [fx for fx in shipping_info_of_items if fx['asin'] == item['id']]

        if len(item_shipping_info) == 0:
            print "No shipping information was captured for %s" % item['id']
            logging.debug(
                "No shipping information was captured for %s",
                item['id']
            )
            return item

        item_shipping_info = item_shipping_info[0]
        item['local_cost'] = item_shipping_info['shipping_cost'] * usd_to_kes.rate
        item['name'] = item_shipping_info['title']
        item['shipping_cost'] = item_shipping_info['shipping_cost']
        item['total_shipping_cost'] = item_shipping_info['shipping_cost'] * item['quantity']
        item['shipping_info'] = item_shipping_info
        return item

    user_order['items'] = map(add_shipping_info_to_item, user_order['items'])

    def update_item_information(item):
        """delete id, calculate total_cost and add missing shipping_cost"""
        # reassign the 'id' property and delete it
        # datastore uses 'id' to retrieve the item auto-assigned key
        if 'id' in item:
            item['asin'] = item['id']
            item.pop('id', None)

        # get the item's price in KES
        item['local_price'] = round(item['price'] * usd_to_kes.rate, 2)

        # get total_cost per item
        item['total_cost'] = round(item['price'] * item['quantity'], 2)

        # if shipping info is missing get the default shipping cost
        if 'shipping_info' not in item:
            item['total_shipping_cost'] = item['quantity']
            item['total_shipping_cost'] *= (amazon_items.MINIMUM_WEIGHT * amazon_items.SHIPPING_WEIGHT_CONSTANT)

        return item

    user_order['items'] = map(update_item_information, user_order['items'])
    user_order['exchange_rate'] = usd_to_kes.rate

    # calculate the order's total shipping cost
    item_shipping_costs = [item['total_shipping_cost'] for item in user_order['items']]
    user_order['total_shipping_cost'] = reduce(lambda a, b: a + b, item_shipping_costs, 0.00)

    # calculate the order's total item costs
    cost_per_items = [item['total_cost'] for item in user_order['items']]
    user_order['total_cost'] = reduce(lambda a, b: a + b, cost_per_items, 0.00)

    user_order['total_cost'] = round(user_order['total_cost'], 2)
    user_order['total_shipping_cost'] = round(user_order['total_shipping_cost'], 2)

    # If the total cost of items is more than $800 shipping cost is completely waved
    if user_order['total_cost'] >= 800:
        user_order['waived_shipping_cost'] = user_order['total_shipping_cost']
        user_order['total_shipping_cost'] = 0.00

    user_order['customs'] = round(user_order['total_cost'] * 0.12, 2)
    user_order['vat'] = round(user_order['total_cost'] * 0.16, 2)

    user_order['overall_cost'] = reduce(lambda a, b: a + b, [
        user_order['total_cost'],
        user_order['total_shipping_cost'],
        user_order['customs'],
        user_order['vat']
    ], 0.00)
    user_order['overall_cost'] = round(user_order['overall_cost'], 2)
    user_order['local_overall_cost'] = user_order['overall_cost'] * user_order['exchange_rate']
    user_order['markup'] = round((user_order['overall_cost'] / user_order['total_cost']) - 1, 2)

    # remove shipping_info from the item dictionary
    user_order['items'] = map(lambda item: (item.pop('shipping_info', None) is True) or item, user_order['items'])

    payload = json.dumps(user_order)
    return Response(payload, status=200, mimetype='application/json')
