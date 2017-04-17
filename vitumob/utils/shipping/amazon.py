import hmac
import hashlib
import base64
import datetime
import urllib
from math import ceil
from functools import reduce
from bs4 import BeautifulSoup

import requests
import requests_toolbelt.adapters.appengine
# Use the App Engine Requests adapter.
# This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()


class AmazonShippingInfo(object):
    AWS_ACCESS_KEY_ID = 'AKIAI6DWQQP2AACCGI6A'
    AWS_SECRET_KEY = '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'
    AWS_ENDPOINT = 'http://webservices.amazon.com/onca/xml'

    MINIMUM_WEIGHT = 2.20462
    SHIPPING_WEIGHT_CONSTANT = 7.5
    VOLUMETRIC_WEIGHT_CONSTANT = 6000
    NONE_PRIME_ITEM_CHARGE = 5.00

    def __init__(self, items):
        self.items = items

    def get_shipping_info(self):
        start = 0
        slice_here = 10
        loops = ceil(len(self.items) / 10)
        loops = 1 if loops < 1 else loops + 1

        slices = []
        for loop in range(int(loops)):
            slices.append(self.items[start:slice_here])
            start += 10
            slice_here += 10

        shipping_info = []
        return reduce(self.fetch_shipping_info, slices, shipping_info)

    @classmethod
    def fetch_shipping_info(cls, shipping_info, items):
        iso_datetime = datetime.datetime.now().isoformat()
        query_params = {
            'AWSAccessKeyId': cls.AWS_ACCESS_KEY_ID,
            'Service': 'AWSECommerceService',
            'AssociateTag': 'vit09-20',
            'Operation': 'ItemLookup',
            'ItemId': ','.join([item['id'] for item in items]),
            'ResponseGroup': 'ItemAttributes,OfferFull',
            # 2017-02-21T14:11:56Z'
            'Timestamp': "{}Z".format(iso_datetime.split('.')[0]),
        }

        query_params_string = urllib.urlencode(query_params).split('&')
        query_params_string.sort()

        query_params_string = '&'.join(query_params_string)
        string_to_sign = "GET\nwebservices.amazon.com\n/onca/xml\n{}".format(query_params_string)
        hash_buffer = hmac.new(cls.AWS_SECRET_KEY, string_to_sign, hashlib.sha256)
        query_params['Signature'] = base64.b64encode(hash_buffer.digest())
        rest_api_endpoint = "{}?{}".format(cls.AWS_ENDPOINT, urllib.urlencode(query_params))

        try:
            soap_response = requests.get(rest_api_endpoint)
            soap_response.raise_for_status()
            batch_items_shipping_info = cls.extract_shipping_information(soap_response.text)
            return shipping_info + batch_items_shipping_info
        except requests.HTTPError:
            raise requests.HTTPError

    @classmethod
    def extract_shipping_information(cls, soap_response):
        # date = datetime.datetime.now().isoformat()
        # xml_file = open("amazon-{}Z.xml".format(date.split('.')[0]), "w")
        # xml_file.write(soap_response.encode('utf-8'))
        # xml_file.close()

        soup = BeautifulSoup(soap_response.encode('utf-8'), 'xml')
        items = soup.find_all('Item')

        def switch(units, value):
            return {
                'ounces': value * 0.0283495,
                'inches': value * 2.54,
                'pounds': value * 0.453592
            }.get(units, value)

        def get_shipping_info(item):
            shipping_info = {}
            if item.find('PackageDimensions') and len(item.PackageDimensions.contents) > 0:
                for value in item.PackageDimensions.contents:
                    unit = value['Units'].replace('hundredths-', '')
                    in_hundreths = 'Units' in value.attrs and 'hundredths' in value[
                        'Units']
                    val = float(value.text) / \
                        100 if in_hundreths else float(value.text)
                    shipping_info[value.name.lower()] = switch(unit, val)

                # volumetric weight = w * h * l / 6000
                volumetric_weight = shipping_info['height']
                volumetric_weight *= shipping_info['width']
                volumetric_weight *= shipping_info['length']
                volumetric_weight /= cls.VOLUMETRIC_WEIGHT_CONSTANT

                # select the greater weight of the two
                if volumetric_weight > shipping_info['weight']:
                    shipping_info['shipping_cost'] = volumetric_weight
                else:
                    shipping_info['shipping_cost'] = shipping_info['weight']

                # with the greater weight selected
                # get the total shipping cost of the weight
                shipping_info['shipping_cost'] *= cls.SHIPPING_WEIGHT_CONSTANT
            else:
                # default weight: 1kg == 2.20462 pounds
                shipping_info['shipping_cost'] = cls.MINIMUM_WEIGHT
                shipping_info['shipping_cost'] *= cls.SHIPPING_WEIGHT_CONSTANT

            # check if the item is a prime item
            is_prime_item = item.find('IsEligibleForPrime')
            if is_prime_item.text != '1':
                shipping_info['shipping_cost'] += cls.NONE_PRIME_ITEM_CHARGE

            shipping_info['asin'] = item.ASIN.text.encode('utf-8')
            shipping_info['title'] = item.ItemAttributes.Title.text.encode('utf-8')
            shipping_info['is_prime_item'] = True if is_prime_item.text == '1' else False
            return shipping_info

        return map(get_shipping_info, items)
