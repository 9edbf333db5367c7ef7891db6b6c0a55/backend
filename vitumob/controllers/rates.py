"""Forex exchange updating"""

import os
import math
import bson
import json
import requests
import requests_toolbelt.adapters.appengine

from bson import json_util
from datetime import datetime
from flask import Blueprint, Response
from json import dumps
from mongoengine import *

from ..models.rates import Rates, Currency

requests_toolbelt.adapters.appengine.monkeypatch()
exchangerates = Blueprint("exchangerates", __name__)


@exchangerates.route('/exchange/rates', methods=['GET', 'POST'])
def get_exchange_rates():
    api_id = os.environ.get('OPENEXCHANGE_API_ID')
    exchangerates_endpoint = "https://openexchangerates.org/api/latest.json?app_id={}".format(api_id)

    stored_rates = Rates(api_id=api_id)
    diff_hours = math.floor((datetime.now() - stored_rates.updated_at).seconds / 3600)
    
    list_of_rates = [x for x in stored_rates.to_mongo() if x[0] == 'rates'] #find the first instance of 'rates' from stored_rates which is a list of arrays 
    if diff_hours > 4 or len(list_of_rates) == 0: #finds the number of items of the dictionary value    
        response = requests.get(exchangerates_endpoint)

        if response.status_code != 200:
            return Response(response.text, status=500, mimetype="applications/json")

        response = response.json()
        rates = [Currency(code=currency, rate=rate)
                for currency, rate in response["rates"].items()
                if currency in ["EUR", "GBP", "KES"]]
            
        stored_rates.rates = rates
        stored_rates.save()

    rates = stored_rates.to_mongo()#mongoengine does not support to_dict that is why i changed to to_mongo
    rates.pop("created_at", None)

    payload = json.dumps(rates, default=json_util.default) #the default is for serializing a datetime object to json
    
    return Response(payload, status=200, mimetype="application/json")











