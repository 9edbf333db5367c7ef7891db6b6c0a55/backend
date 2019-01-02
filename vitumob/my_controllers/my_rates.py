"""Forex exchange updating"""

import os
import math
import datetime

from flask import Blueprint, Response
from pymongo import MongoClient

import requests
import requests_toolbelt.adapters.appengine

from ..my_models.my_rates import Currency, Rates
from ..utils import json

requests_toolbelt.adapters.appengine.monkeypatch()
exchangerates = Blueprint("exchangerates", __name__)

@exchangerates.route("/exchange/rates", methods=["GET"])
def get_exchange_rates():
    api_id = os.environ.get("OPENEXCHANGE_API_ID")
    exchangerates_endpoint = "https://openexchangerates.org/api/latest.json?app_id={}".format(
        api_id)
    rates_key = Key(Rates, api_id)
    stored_rates = rates.get_or_insert(rates_key.id())

    diff_hours = math.floor((datetime.now() - stored_rates.updated_at).seconds / 3600)
    if diff_hours > 4 or len(stored_rates.to_dict()["rates"]) <= 0:
        response = requests.get(exchangerates_endpoint)

        if response.status_code != 200:
            return Response(response.text, status=500, mimetype="applications/json")

            response = response.json()
            rates = [Currency(code=currency, rate=rate)
                    for currency, rate in response["rates"].items()
                    if currency in ["EUR", "GBP", "KES"]]

            stored_rates.rates = rates
            stored_rates.put()

        rates = stored_rates.to_dict()
        rates.pop("created_at", None)

        payload = json.dumps(rates)
        return Response(payload, status=200, mimetype="application/json")
