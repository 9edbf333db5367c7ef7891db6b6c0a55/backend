"""Forex exchange updating"""

import os
import math
from datetime import datetime

from flask import Blueprint, Response
from google.appengine.ext import ndb

import requests
import requests_toolbelt.adapters.appengine

from ..models.rates import Currency, Rates
from ..utils import ndb_json


requests_toolbelt.adapters.appengine.monkeypatch()
exchangerates = Blueprint('exchangerates', __name__)


@exchangerates.route('/exchange/rates', methods=['GET'])
def get_exchange_rates():
    api_id = os.environ.get('OPENEXCHANGE_API_ID')
    exchangerates_endpoint = "https://openexchangerates.org/api/latest.json?app_id=%s" % api_id

    rates_key = ndb.Key(Rates, api_id)
    stored_rates = Rates.get_or_insert(rates_key.id())

    diff_hours = math.floor((datetime.now() - stored_rates.updated_at).seconds / 3600)
    if diff_hours > 4 or len(stored_rates.to_dict()['rates']) <= 0:
        payload = requests.get(exchangerates_endpoint)
        payload.raise_for_status()
        payload = payload.json()

        rates = [Currency(code=currency, rate=rate)
                 for currency, rate in payload['rates'].items()
                 if currency in ['EUR', 'GBP', 'KES']]

        stored_rates.rates = rates
        stored_rates.put()

    rates = stored_rates.to_dict()
    rates.pop('created_at', None)

    payload = ndb_json.dumps(rates)
    return Response(payload, status=200, mimetype='application/json')
