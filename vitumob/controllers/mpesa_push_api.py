import os
import json
import time
import logging
import base64
from datetime import datetime
from flask import Blueprint, Response, request

import requests
import requests_toolbelt.adapters.appengine
from requests.auth import HTTPBasicAuth

from google.appengine.ext import ndb

from ..models.user import User
from ..models.order import Order
from ..models.mpesa import MpesaDarajaAccessToken, MpesaPayment
from ..utils import ndb_json

requests_toolbelt.adapters.appengine.monkeypatch()
mpesa_push_api = Blueprint('mpesa_push_api', __name__)


# @mpesa_push_api.route('/payments/mpesa/paybill/register_webhooks', methods=['POST'])
def set_completed_and_validation_callbacks(access_token):
    """Set Vitumob's confirmation and validation URLs"""
    register_webhooks_endpoint = "https://api.safaricom.co.ke/mpesa/c2b/v1/registerurl"
    server_endpoint = "https://vitumob-xyz.appspot.com/payments/mpesa"
    vitumob_resource_options = {
        'endpoint': server_endpoint,
    }
    headers = {
        "Host": "api.safaricom.co.ke",
        "Content-Type": "application/json",
        "Authorization": "Bearer {access_token}".format(access_token=access_token)
    }
    payload = {
        "ShortCode": os.environ.get("MPESA_PAYBILL_NUMBER"),
        "ResponseType": "Cancelled",
        "ConfirmationURL": "{endpoint}/payment/complete".format(**vitumob_resource_options),
        "ValidationURL": "{endpoint}/payment/validate".format(**vitumob_resource_options),
    }
    response = requests.post(register_webhooks_endpoint, json=payload, headers=headers)
    logging.debug(response.text)
    return response


@mpesa_push_api.route('/payments/mpesa/token', methods=['GET', 'POST'])
def get_or_update_mpesa_access_token():
    """Get the MPESA DARAJA auth token to be able to make payment requests"""
    api_url = "https://api.safaricom.co.ke/oauth/v1/generate"

    access_token_key = ndb.Key(
        MpesaDarajaAccessToken, os.environ.get("MPESA_DARAJA_API_CONSUMER_KEY")
    )
    access_token = MpesaDarajaAccessToken.get_or_insert(
        access_token_key.string_id()
    )
    now_in_seconds = time.mktime(datetime.now().timetuple())

    if access_token is None or access_token.expiring_time <= now_in_seconds:
        credentials = HTTPBasicAuth(
            os.environ.get("MPESA_DARAJA_API_CONSUMER_KEY"),
            os.environ.get("MPESA_DARAJA_API_CONSUMER_SECRET")
        )
        headers = {
            "Accept": "application/json"
        }
        payload = {
            "grant_type": "client_credentials"
        }
        response = requests.get(api_url, auth=credentials, headers=headers, params=payload)
        output = Response(response.text, status=response.status_code, mimetype='application/json')
        daraja_access_token = response.json()

        if response.status_code == 200:
            cbr = set_completed_and_validation_callbacks(
                daraja_access_token['access_token']
            )

            if cbr.status_code == 200:
                # access_token = MpesaDarajaAccessToken(**response.json())
                access_token.populate(
                    access_token=daraja_access_token['access_token'],
                    expires_in=int(daraja_access_token['expires_in'])
                )
                access_token.put()
                return output

            return Response(cbr.text, status=cbr.status_code, mimetype='application/json')

        return output

    payload = ndb_json.dumps(access_token)
    return Response(payload, status=200, mimetype='application/json')


@mpesa_push_api.route('/payments/mpesa/payment/request', methods=['POST'])
def simulate_payment_via_mpesa_stk_push():
    """
    Simulate invoking of a payment to MPESA, which will then hit your payment
    validation and completion callback endpoints
    """
    endpoint = "https://api.safaricom.co.ke/mpesa/c2b/v1/simulate"
    access_token = request.headers['Authorization']
    headers = {
        # "Host": "api.safaricom.co.ke",
        "Content-Type": "application/json",
        "Authorization": "Bearer {access_token}".format(access_token=access_token)
    }
    data = {
        "ShortCode": os.environ.get("MPESA_PAYBILL_NUMBER"),
        "CommandID": "CustomerPayBillOnline",
        "Amount": "100",
        "Msisdn": "254723001575",
        "BillRefNumber": "account"
    }
    response = requests.post(endpoint, json=data, headers=headers)
    # {
    #     "ConversationID": "AG_20181023_0000410980fe88c4e31d",
    #     "OriginatorCoversationID": "16419-9105748-1",
    #     "ResponseDescription": "Accept the service request successfully."
    # }
    return Response(response.text, status=response.status_code, mimetype='application/json')


@mpesa_push_api.route('/payments/mpesa/payment/push/<string:order_id>', methods=['POST'])
def request_payment_via_mpesa_stk_push(order_id):
    daraja_stk_push_endpoint = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    order_key = ndb.Key(Order, ndb.Key(urlsafe=order_id).id())
    order = Order.get_by_id(order_key.id())

    if order is not None:
        order = order.to_dict()
        order['id'] = order.key.id()

        user = order.user.get()
        order['user_phone_number'] = user.phone_number
    else:
        order = request.get_json()

    access_token = request.headers['Authorization']
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {access_token}".format(access_token=access_token)
    }

    timestamp = time.strftime("%Y%m%d%H%M%S")
    base64_encoded_password = base64.b64encode("".join([
        os.environ.get("MPESA_PAYBILL_NUMBER"),
        os.environ.get("MPESA_PAYBILL_PASSKEY"),
        timestamp
    ]))

    payload = {
        "BusinessShortCode": os.environ.get("MPESA_PAYBILL_NUMBER"),
        # This is generated by base64 encoding BusinessShortcode, Passkey and Timestamp"
        "Password": base64_encoded_password,
        "Timestamp": timestamp,  # format yyyymmddhhiiss",
        "TransactionType": "CustomerPayBillOnline",
        # "Amount": int(order_id) / 300,
        "Amount": order['amount'] if 'amount' in order else order['local_overall_cost'],
        # "PartyA": '254723001575',
        "PartyA": order['user_phone_number'],
        "PartyB": os.environ.get("MPESA_PAYBILL_NUMBER"),
        # "PhoneNumber": '254723001575',
        "PhoneNumber": order['user_phone_number'],
        "CallBackURL": "https://vitumob-xyz.appspot.com/payments/mpesa/confirm",
        # "AccountReference": str(order_id),
        "AccountReference": order['id'],
        "TransactionDesc": "Payment for ORDER: {order_id}".format(order_id=order['id'])
    }
    logging.debug(json.dumps(payload))
    response = requests.post(daraja_stk_push_endpoint, json=payload, headers=headers)z
    # {
    #     "CheckoutRequestID": "ws_CO_DMZ_105178180_23102018082038007",
    #     "CustomerMessage": "Success. Request accepted for processing",
    #     "MerchantRequestID": "11138-7024993-1",
    #     "ResponseCode": "0",
    #     "ResponseDescription": "Success. Request accepted for processing"
    # }

    if response.status_code == 200:
        payment_key = ndb.Key(MpesaPayment, response.json['MerchantRequestID'])
        new_mpesa_payment = MpesaPayment.get_or_insert(payment_key.string_id())
        new_mpesa_payment.populate(order_id=order['id'], user_id=str(user.key.id()))

        # save the mpesa payment and add the key to the order
        if order is not None:
            order.mpesa_payment = new_mpesa_payment.put()
            order.put()
        else:
            new_mpesa_payment.put()

    return Response(response.text, status=response.status_code, mimetype='application/json')


def get_from(data, name_of_property):
    """Helper array filter function"""
    data = [x['Name'] for x in data if x['Name'] == name_of_property]
    return data[0] if len(data) > 0 else None


@mpesa_push_api.route('/payments/mpesa/payment/complete', methods=['POST'])
def payment_completed_webhook():
    """The callback called by the Safaricom Daraja API when the user completes a payment"""
    payment_info = request.get_json() if request.is_json() else None

    if payment_info is not None:
        payment_info = payment_info['Body']['stkCallback']
        payment_key = ndb.Key(MpesaPayment, payment_info['MerchantRequestID'])
        new_mpesa_payment = MpesaPayment.get_or_insert(payment_key.string_id())

        payment_metadata = payment_info['CallbackMetadata']['Item']
        logging.debug(json.dumps(request.json))

        mpesa_payment = {
            "amount": get_from(payment_metadata, "Amount"),
            "code": get_from(payment_metadata, "MpesaReceiptNumber"),
            "phone_no": get_from(payment_metadata, "PhoneNumber"),
            "merchant_request_id": payment_info['MerchantRequestID'],
            "checkout_request_id": payment_info['CheckoutRequestID']
        }

        new_mpesa_payment.populate(**mpesa_payment)
        new_mpesa_payment.put()
        logging.debug(json.dumps(mpesa_payment))

        # forward teh payment to Vitumob hostgator servers
        timestamp_as_string = get_from(payment_metadata, "TransactionDate")
        datetime_parsed = datetime.strptime(str(timestamp_as_string), '%Y%m%d%H%M%S')
        payload = {
            "id": payment_info['MerchantRequestID'],
            "orig": "MPESA",
            "dest": os.environ.get("MPESA_PAYBILL_NUMBER"),
            "tstamp": datetime_parsed.strftime("%Y-%m-%d+%H:%M:%S"),
            "text": json.dumps(payment_info),
            # "customer_id": new_mpesa_payment.user_id,
            "user": "safaricom",
            "pass": base64.b64encode(time.strftime("%Y%m%d%H%M%S")),
            "routemethod_id": 2,
            "routemethod_name": "HTTP",
            "mpesa_code": mpesa_payment['code'],
            "mpesa_acc": new_mpesa_payment.order_id,
            "mpesa_msisdn": mpesa_payment['phone_no'],
            "mpesa_trx_date": datetime_parsed.strftime("%d/%m/%Y"),
            "mpesa_trx_time": datetime_parsed.strftime("%I:%M+%p"),
            "mpesa_amt": get_from(payment_metadata, "Amount"),
            "mpesa_sender": mpesa_payment['phone_no'],
            "business_number": os.environ.get("MPESA_PAYBILL_NUMBER"),
            # Missing - dest, text, customer_id, pass, mpesa_trx_date, mpesa_trx_time
        }
        logging.debug("forwarding mpesa payment info to hostgator: {}".format(json.dumps(payload)))

        firebase_endpoint = 'https://vitumob-xyz.firebaseio.com'
        firebase_resource = "{firebase_endpoint}/payments/mpesa/{order_id}.json".format(
            firebase_endpoint=firebase_endpoint,
            order_id=new_mpesa_payment.order_id
        )

        response = requests.post(firebase_resource, data=payload)
        if response.status_code == 200:
            logging.info("Mpesa payment successful response forwarded to FIREBASE {}".format(
                json.dumps(payload)
            ))

        vitumob_hostgator_mpesa_callback_url = "https://vitumob.com/mpesa"
        response = request.get(vitumob_hostgator_mpesa_callback_url, params=payload)
        return Response(json.dumps(payload), status=response.status_code, mimetype='application/json')

    return Response('{}', status=200, mimetype='application/json')
