import os
import hmac
import hashlib
import base64
import datetime
import urllib
import random
import json

import requests
import requests_toolbelt.adapters.appengine
# Use the App Engine Requests adapter.
# This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()


class ItemShippingInfo(object):
    MINIMUM_WEIGHT = 2.20462
    SHIPPING_WEIGHT_CONSTANT = 7.50
    VOLUMETRIC_WEIGHT_CONSTANT = 6000
    NONE_PRIME_ITEM_CHARGE = 5.00

    def __init__(self, items):
        self.items = items

    def retrieve_shipping_info(self):
        items_shipping_info = map(self.get_item_shipping_info, self.items)
        error_found = [x for x in items_shipping_info if x[1] not in [200, 201]]

        if len(error_found) > 0:
            return error_found[0]

        return ([x[0] for x in items_shipping_info], 200)

    @classmethod
    def get_item_shipping_info(cls, item):
        query_params = {
            'searchKey': item['id'],
            'language': 'en_US',
            'profitcalcToken': os.getenv('AWS_SELLERS_CENTRAL_TOKENS')[random.randint(0, 2)]
        }
        rest_api_endpoint = "{endpoint}?{query_params}".format(
            endpoint=os.environ.get("AWS_SELLERS_CENTRAL_ENDPOINT"),
            query_params=urllib.urlencode(query_params)
        )
        response = requests.get(rest_api_endpoint)
        if response.status_code in [200, 201]:
            item_meta_data = response.json()
            item_shipping_info = cls.extract_item_shipping_info(item_meta_data['data'][0])
            return (item_shipping_info, response.status_code,)

        return (response.text, response.status_code,)

    @classmethod
    def convert_metric_to_local(cls, unit, value):
        to_local_metrics_options = {
            'ounces': value * 0.0283495,
            'inches': value * 2.54,
            'pounds': value * 0.453592
        }
        return to_local_metrics_options.get(unit, value)

    @classmethod
    def extract_item_shipping_info(cls, item_shipping_info):
        shipping_info = {}
        shipping_info['is_prime_item'] = True

        if item_shipping_info['width'] is not 0 or item_shipping_info['weight'] is not 0:
            # volumetric weight = w * h * l / 6000
            item_dimension_unit = item_shipping_info['dimensionUnit']
            volumetric_weight = cls.convert_metric_to_local(item_dimension_unit, item_shipping_info['height'])
            volumetric_weight *= cls.convert_metric_to_local(item_dimension_unit, item_shipping_info['width'] )
            volumetric_weight *= cls.convert_metric_to_local(item_dimension_unit, item_shipping_info['length'])
            volumetric_weight /= cls.VOLUMETRIC_WEIGHT_CONSTANT

            # select the greater weight of the two
            item_weight = cls.convert_metric_to_local(item_shipping_info['weightUnit'], item_shipping_info['weight'])
            if volumetric_weight > item_weight:
                shipping_info['shipping_cost'] = volumetric_weight
            else:
                shipping_info['shipping_cost'] = item_weight

            # with the greater weight selected
            # get the total shipping cost of the weight
            shipping_info['shipping_cost'] *= cls.SHIPPING_WEIGHT_CONSTANT
        else:
            # minumum weight: 1kg == 2.20462 pounds
            shipping_info['shipping_cost'] = cls.MINIMUM_WEIGHT
            shipping_info['shipping_cost'] *= cls.SHIPPING_WEIGHT_CONSTANT

        # check if the item is a prime item
        if 'prime' not in item_shipping_info:
            shipping_info['shipping_cost'] += cls.NONE_PRIME_ITEM_CHARGE
            shipping_info['is_prime_item'] = False

        shipping_info['asin'] = item_shipping_info['asin']
        shipping_info['title'] = item_shipping_info['title']
        return shipping_info
