"""Payments processing"""

import os
import time
import json
import logging

from datetime import datetime
from flask import Blueprint, Response, request
# from google.appengine.api import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext import ndb

import requests
from requests.auth import HTTPBasicAuth
import requests_toolbelt.adapters.appengine

from ..models.order import Order
from ..models.paypal import PayPalToken, PayPalPayment, PayPalPayer
from ..models.rates import Rates
from ..utils import ndb_json


requests_toolbelt.adapters.appengine.monkeypatch()
paypal_payments = Blueprint('paypal_payments', __name__)


@paypal_payments.route('/payments/paypal/token', methods=['GET'])
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


@paypal_payments.route('/payments/paypal/create/<string:order_id>', methods=['POST'])
def execute_paypal_payment(order_id):
    """
    Initialise a payment, returning an approval URL to redirect or
    take the user to approve the payment
    """
    order = ndb.Key(Order, ndb.Key(urlsafe=order_id).id())
    order = order.get()

    access_token = request.headers['Authorization']
    paypal_payment_resource = 'https://api.sandbox.paypal.com/v1/payments/payment'
    server_endpoint = 'https://{application_id}.appspot.com/payments/paypal'.format(
        application_id=os.environ.get("APPENGINE_SERVER")
    )
    vitumob_resource_options = {
        'endpoint': server_endpoint,
        'order_id': order_id
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {access_token}".format(access_token=access_token)
    }

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
                "note_to_payee": "{message} (Order ID: {order_id})".format(
                    message="Contact us for any questions/queries/concerns on your order",
                    order_id=order_id
                ),
                # "notify_url": "{endpoint}/notifications".format(endpoint=vm_endpoint)
            }
        ],
        "redirect_urls": {
            "return_url": "{endpoint}/approved/{order_id}".format(**vitumob_resource_options),
            "cancel_url": "{endpoint}/cancelled/{order_id}".format(**vitumob_resource_options)
        },
    }
    logging.debug(json.dumps(headers))
    response = requests.post(paypal_payment_resource, headers=headers, json=payment_info)

    if response.status_code == 201:
        rates_key = ndb.Key(Rates, os.environ.get('OPENEXCHANGE_API_ID'))
        rates = Rates.get_by_id(rates_key.id())
        usd_to_kes = [rate for rate in rates.rates if rate.code == 'KES'][0]

        payment_details = response.json()
        payment = {
            'id': payment_details['id'],
            # create_time => 2017-04-25T23:41:47Z
            'create_time': datetime.strptime(payment_details['create_time'], "%Y-%m-%dT%H:%M:%SZ"),
            'amount': order.overall_cost,
            'local_amount': order.overall_cost * usd_to_kes.rate
        }
        payment = PayPalPayment(**payment)
        order.paypal_payment = payment.put()
        order.put()

        payload = json.dumps({'links': payment_details['links']})
        return Response(payload, status=response.status_code, mimetype='application/json')

    # something went wrong if this is returned
    return Response(response.text, status=response.status_code, mimetype='application/json')


def sync_paypal_payment_to_hostgator(endpoint, order_key):
    """Sync a user's PayPal payment of an order to Hostgator"""
    order = order_key.get()

    payment = order.paypal_payment.get()
    payment_payload = payment.to_dict()
    payment_payload['id'] = payment.key.id()
    payment_payload['user_id'] = order.user.get().key.id()
    payment_payload['order_id'] = order.key.id()
    payload = ndb_json.dumps({
        'payment': payment_payload,
    })
    logging.info("Payload: {}".format(payload))
    resource = '{endpoint}/order/{order_id}/payment'.format(
        endpoint=endpoint,
        order_id=order.key.id()
    )
    response = requests.post(resource, data=payload)
    logging.info("Response Status Code: {status_code}, Response Body: {body}".format(
        status_code=response.status_code,
        body=response.text
    ))


# https://vitumob.xyz/payments/paypal/approved/aghkZXZ-Tm9uZXISCxIFT3JkZXIYgICAgIDg9wkM
# ?paymentId=PAY-5DW7657589732850VLD75OSI&token=EC-0WU786306C7964538&PayerID=R6NVJ4B97J9G2
@paypal_payments.route('/payments/paypal/approved/<string:order_id>', methods=['GET'])
def user_approved_paypal_payment(order_id):
    """
    If the user approves the payment, the user is redirected to
    this page where we then order paypal to execute the payment approved.
    """
    order = ndb.Key(Order, ndb.Key(urlsafe=order_id).id())
    order = order.get()

    token_key = ndb.Key(PayPalToken, os.environ.get("PAYPAL_CLIENT_ID"))
    token = PayPalToken.get_by_id(token_key.id())

    # POST https://api.sandbox.paypal.com/v1/payments/payment/PAY-34629814WL663112AKEE3AWQ/execute
    if request.args.get('token') and request.args.get('paymentId'):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {access_token}".format(access_token=token.access_token)
        }
        data = {
            'payer_id': request.args.get('PayerID')
        }
        paypal_endpoint = 'https://api.sandbox.paypal.com/v1/payments/payment'
        pp_payment_execusion_resource = "{paypal_endpoint}/{payment_id}/execute".format(
            paypal_endpoint=paypal_endpoint,
            payment_id=request.args.get('paymentId')
        )
        response = requests.post(pp_payment_execusion_resource, headers=headers, json=data)
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

            payment = order.paypal_payment.get()
            payment.client = PayPalPayer(**payer)
            payment.put()

            order.is_temporary = False
            order.put()

            # taskqueue.add(
            #     url='/order/{order_id}/payment'.format(order_id=order.key.id()),
            #     method='PUT',
            #     target='worker',
            # )

            endpoint = os.environ.get("HOSTGATOR_SYNC_ENDPOINT")
            deferred.defer(sync_paypal_payment_to_hostgator, endpoint, order.key)

            payload = ndb_json.dumps(payment)
            return Response(payload, status=response.status_code, mimetype='application/json')

        # The payment execusion failed
        return Response(response.text, status=response.status_code, mimetype='application/json')

    payload = json.dumps({'status': 401, 'message': 'Payment processing failed'})
    return Response(payload, status=401, mimetype='application/json')


@paypal_payments.route('/payments/paypal/cancelled/<string:order_id>', methods=['GET'])
def user_cancelled_paypal_payment(order_id):
    """If the user cancels or does not make the payment, the user will be redirected to this URL"""
    payload = json.dumps({'status': 403, 'message': 'User Cancelled Payment!'})
    return Response(payload, status=403, mimetype='application/json')
