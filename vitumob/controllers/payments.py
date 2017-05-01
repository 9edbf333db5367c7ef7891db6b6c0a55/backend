"""Payments processing"""

import os
import time
import json
import logging

from datetime import datetime
from flask import Blueprint, Response, request
from google.appengine.ext import ndb

import requests
from requests.auth import HTTPBasicAuth
import requests_toolbelt.adapters.appengine

from ..models.order import Order
from ..models.paypal import PayPalToken, PayPalPayment, PayPalPayer
from ..models.rates import Rates
from ..utils import ndb_json


requests_toolbelt.adapters.appengine.monkeypatch()
payments = Blueprint('payments', __name__)


@payments.route('/payments/paypal/token', methods=['GET'])
def create_paypal_payment():
    """Get or update the PayPal token we'll use in creating and executing payments"""
    endpoint = 'https://api.sandbox.paypal.com/v1/oauth2/token'

    token_key = ndb.Key(PayPalToken, os.environ.get("PAYPAL_CLIENT_ID"))
    token = PayPalToken.get_or_insert(token_key.string_id())

    now_in_seconds = time.mktime(datetime.now().timetuple())
    if token is None or token.expiring_time <= now_in_seconds:
        credentials = HTTPBasicAuth(
            os.environ.get("PAYPAL_CLIENT_ID"),
            os.environ.get("PAYPAL_SECRET_KEY")
        )
        headers = {
            'Accept-Language': 'en_US',
            'Accept': 'application/json'
        }
        payload = {
            'grant_type': 'client_credentials'
        }
        response = requests.post(endpoint, auth=credentials, headers=headers, data=payload)

        if response.status_code == 200:
            # token = PayPalToken(**response.json())
            token.populate(**response.json())
            token.put()

        return Response(response.text, status=response.status_code, mimetype='application/json')

    payload = ndb_json.dumps(token)
    return Response(payload, status=200, mimetype='application/json')


@payments.route('/payments/paypal/create/<string:order_id>', methods=['POST'])
def execute_paypal_payment(order_id):
    """Initialises a payment, returning an approval URL to redirect or take the user to approve the payment"""
    order = ndb.Key(Order, ndb.Key(urlsafe=order_id).id())
    order = order.get()

    access_token = request.headers['Authorization']
    endpoint = 'https://api.sandbox.paypal.com/v1/payments/payment'
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {access_token}".format(access_token=access_token)
    }

    note_to_payee = "{info} (Order ID: {order_id})".format(
        info="Contact us for any questions on your order",
        order_id=order_id
    )
    payment_info = {
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [
            {
                "amount": {
                    "total": "{}".format(order.overall_cost),
                    "currency": "USD"
                },
                "description": "VituMob - Everything Everyday.",
                "note_to_payee": note_to_payee,
                # "notify_url": "https://vitumob.xyz/payments/paypal/notifications"
            }
        ],
        "redirect_urls": {
            "return_url": "https://vitumob.xyz/payments/paypal/approved/%s" % order_id,
            "cancel_url": "https://vitumob.xyz/payments/paypal/cancelled/%s" % order_id
        },
    }
    logging.debug(json.dumps(headers))
    logging.debug(json.dumps(payment_info))
    response = requests.post(endpoint, headers=headers, json=payment_info)

    if response.status_code == 201:
        payment_details = response.json()
        payment = {
            'id': payment_details['id'],
            # create_time => 2017-04-25T23:41:47Z
            'create_time': datetime.strptime(payment_details['create_time'], "%Y-%m-%dT%H:%M:%SZ"),
            'amount': order.overall_cost,
        }
        payment = PayPalPayment(**payment)
        order.payment = payment.put()
        order.put()

    return Response(response.text, status=response.status_code, mimetype='application/json')


# https://vitumob.xyz/payments/paypal/approved/aghkZXZ-Tm9uZXISCxIFT3JkZXIYgICAgIDg9wkM
# ?paymentId=PAY-5DW7657589732850VLD75OSI&token=EC-0WU786306C7964538&PayerID=R6NVJ4B97J9G2
@payments.route('/payments/paypal/approved/<string:order_id>', methods=['GET'])
def user_approved_paypal_payment(order_id):
    """
    If the user approves the payment, the user is redirected to
    this page where we then order paypal to execute the payment approved.
    """
    order = ndb.Key(Order, ndb.Key(urlsafe=order_id).id())
    order = order.get()

    token_key = ndb.Key(PayPalToken, os.environ.get("PAYPAL_CLIENT_ID"))
    token = PayPalToken.get_by_id(token_key.id())

    rates_key = ndb.Key(Rates, os.environ.get('OPENEXCHANGE_API_ID'))
    rates = Rates.get_by_id(rates_key.id())
    usd_to_kes = [rate for rate in rates.rates if rate.code == 'KES'][0]

    # POST https://api.sandbox.paypal.com/v1/payments/payment/PAY-34629814WL663112AKEE3AWQ/execute
    if request.args.get('token') and request.args.get('paymentId'):
        paypal_endpoint = 'https://api.sandbox.paypal.com/v1/payments/payment'
        endpoint = "{paypal_endpoint}/{payment_id}/execute".format(
            paypal_endpoint=paypal_endpoint,
            payment_id=request.args.get('paymentId')
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {access_token}".format(access_token=token.access_token)
        }
        data = {
            'payer_id': request.args.get('PayerID')
        }
        response = requests.post(endpoint, headers=headers, json=data)
        payment_info = response.json()

        if response.status_code == 200 and payment_info['state'] == 'approved':
            payer = {}
            payer_info = payment_info['payer']['payer_info']

            if payer_info['first_name'] is not None:
                payer['first_name'] = payer_info['first_name']

            if payer_info['last_name'] is not None:
                payer['last_name'] = payer_info['last_name']

            payer['id'] = payer_info['payer_id']
            payer['email'] = payer_info['email']
            payer['payment_method'] = payment_info['payer']['payment_method']

            payment = order.payment.get()
            payment.local_amount = order.overall_cost * usd_to_kes.rate
            payment.client = PayPalPayer(**payer)
            payment.put()

            order.is_temporary = False
            order.put()

            payload = ndb_json.dumps(payment)
            return Response(payload, status=response.status_code, mimetype='application/json')

        return Response(response.text, status=response.status_code, mimetype='application/json')

    payload = json.dumps({'status': 401, 'message': 'Payment processing failed'})
    return Response(payload, status=401, mimetype='application/json')


@payments.route('/payments/paypal/cancelled/<string:order_id>', methods=['GET'])
def user_cancelled_paypal_payment(order_id):
    """If the user cancels or does not make the payment, the user will be redirected to this URL"""
    payload = json.dumps({'status': 403, 'message': 'User Cancelled Payment!'})
    return Response(payload, status=403, mimetype='application/json')
