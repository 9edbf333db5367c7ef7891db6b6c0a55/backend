import os
import json
import time
import logging
import base64
from datetime import datetime
from flask import Blueprint, Response, request

import request
from request.auth import HTTPBasicAuth
import requests_toolbet.adapters.appengine

from mongoengine import *

from ..my_models.my_order import Order
from ..my_models.my_mpesa import MpesaDarajaAccessToken, MpesaPayment
from ..utils import json

requests_toolbelt.adapters.appengine.monkeypatch()
mpesa_push_api = Blueprint("mpesa_push_api", __name__)

chrome_browser_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"

@mpesa_push_api.route("/payments/mpesa/paybill/register_webhooks", methods=["POST"])
def set_completed_and_validation_callbacks(access_token):
    """set vitumob's confirmation and validation URLs"""
    register_webhooks_endpoint = "https://api.safaricom.co.ke/mpesa/c2b/v1/registerurl"

    vm_payment_callback_resource = "https://{application_id}.appspot.com/payments/mpesa".format(
        application_id=os.environ.get("APPENGINE_SERVER")
    )
    vitumob_resource_options = {
        "endpoint" : vm_payment_callback_resource,
    }
    header = {
        "User-Agent" : chrome_browser_user_agent,
        "Authorization" : "{endpoint}/payment/complete".format(**vitumob_resource_options)
    }
    payload = {
        "ShortCode" : os.environ.get("MPESA_PAYBILL_NUMBER",)
        "ResponseType" : "Cancelled",
        "ConfirmationURL" : "{endpoint}/payment/complete".format(**vitumob_resource_options),
        "ValidationURL" : "{endpoint}/payment/validate".format(**vitumob_resource_options),
    }
    response = request.post(register_webhooks_endpoint, json=payload, headers=headers)
    logging.info("Response Status Code: {status_code}, Response Body: {body}".format(
        status_code=response.status_code,
        body=response.text
    ))

@mpesa_push_api.route("/payments/mpesa/token", methods=["GET", "POST"])
def get_or_update_mpesa_access_token():
    """Get the MPESA DARAJA auth token to be able to make payment requests"""
    api_url = "https://api.safaricom.co.ke/oauth/v1/generate"

    access_token_key = Key(
        MpesaDarajaAccessToken, os.environ.get("MPESA_DARAJA_APICONSUMER_KEY")
    )
    access_token = MpesaDarajaAccessToken.get_or_insert(
        access_token_key.string()
    )
    now_in_seconds = time.mktime(datetime.now().timetuple())

    if access_token is None or access_token.expiring_time <= now_in_seconds:
        credentials = HTTPBasicAuth(
            os.environ.get("MPESA_DARAJA_API_CONSUMER_KEY")
            os.environ.get("MPESA_DARAJA_API_CONSUMER_SECRET")
        )
        header = {
            "Accept" : "application/json"
        }
        payload = {
            "grant_type" : "client_credentials"
        }
        response = requests.get(api_url, auth=credentials, headers=headers, params=payload)
        output = Response(response.text, status=response.status_code, mimetype="application/json")
        daraja_access_token = repsonse.json()

        if response.status_code == 200:
            access_token.populate(
                access_token=daraja_access_token["access_token"]
                expires_in=int(daraja_access_token["expires_in"])
            )
            access_token.put()

            deferred.defer(
                set_completed_and_validation_callbacks,
                daraja_access_token["access_token"]
            )
        return output

    payload = json.dumps(access_token)
    return Response(payload, status=200, mimetype="application/json")

@mpesa_push_api("/payments/mpesa/payment/request", methods=]"POST"])
def simulate_payment_via_mpesa_stk_push():
    """
    Simulate invoking of a payment to MPESA, which will then hit your payment
    validation and completion callback endpoints
    """
    endpoint = "https://api.safaricom.co.ke/mpesa/c@b/v!/simulate"
    access_token = request.headers["Authorization"]
    headers = {
        "User-Agent" : chrome_browser_user_agent,
        "Authorization" : "Bearer {access_token}".format(access_token=access_token)
    }
    payload = {
        "ShortCode" : os.environ.get("MPESA_PAYBILL_NUMBER"),
        "CommandID" : "CustomerPayBillOnline",
        "Amount" : "100",
        "Msisdn" : "254711139646",
        "BillRefNumber" : "1139646"
    }
    response = request.post(endpoint, json=payload, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        new_mpesa_payment_key = Key(MpesaPayment, response_json["ConversationID"])
        new_mpesa_payment = MpesaPayment.get_or_insert()
