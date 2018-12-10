import os
import json
import time
import logging
import base64
# import urllib
from datetime import datetime
from flask import Blueprint, Response, request

import requests
from requests.auth import HTTPBasicAuth
import requests_toolbelt.adapters.appengine

# from google.appengine.api import urlfetch
from google.appengine.ext import deferred
from google.appengine.ext import ndb

# from ..models.user import User
# from ..models.order import Order
from ..models.mpesa import MpesaDarajaAccessToken, MpesaPayment
from ..utils import ndb_json

requests_toolbelt.adapters.appengine.monkeypatch()
mpesa_push_api = Blueprint('mpesa_push_api', __name__)

chrome_browser_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"


# @mpesa_push_api.route('/payments/mpesa/paybill/register_webhooks', methods=['POST'])
def set_completed_and_validation_callbacks(access_token):
    """Set Vitumob's confirmation and validation URLs"""
    register_webhooks_endpoint = "https://api.safaricom.co.ke/mpesa/c2b/v1/registerurl"
    vm_payment_callback_resource = "https://{application_id}.appspot.com/payments/mpesa".format(
        application_id=os.environ.get("APPENGINE_SERVER")
    )
    vitumob_resource_options = {
        "endpoint": vm_payment_callback_resource,
    }
    headers = {
        # "Content-Type": "application/json",
        "User-Agent": chrome_browser_user_agent,
        "Authorization": "Bearer {access_token}".format(access_token=access_token)
    }
    payload = {
        "ShortCode": os.environ.get("MPESA_PAYBILL_NUMBER"),
        "ResponseType": "Cancelled",
        "ConfirmationURL": "{endpoint}/payment/complete".format(**vitumob_resource_options),
        "ValidationURL": "{endpoint}/payment/validate".format(**vitumob_resource_options),
    }
    response = requests.post(register_webhooks_endpoint, json=payload, headers=headers)
    logging.info("Response Status Code: {status_code}, Response Body: {body}".format(
        status_code=response.status_code,
        body=response.text
    ))


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
            # access_token = MpesaDarajaAccessToken(**response.json())
            access_token.populate(
                access_token=daraja_access_token['access_token'],
                expires_in=int(daraja_access_token['expires_in'])
            )
            access_token.put()

            deferred.defer(
                set_completed_and_validation_callbacks,
                daraja_access_token['access_token']
            )

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
        # "Content-Type": "application/json",
        "User-Agent": chrome_browser_user_agent,
        "Authorization": "Bearer {access_token}".format(access_token=access_token)
    }
    payload = {
        "ShortCode": os.environ.get("MPESA_PAYBILL_NUMBER"),
        "CommandID": "CustomerPayBillOnline",
        "Amount": "575",
        "Msisdn": "254723001575",
        "BillRefNumber": "3001575"
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    # {
    #     "ConversationID": "AG_20181023_0000410980fe88c4e31d",
    #     "OriginatorCoversationID": "16419-9105748-1",
    #     "ResponseDescription": "Accept the service request successfully."
    # }

    if response.status_code == 200:
        response_json = response.json()
        new_mpesa_payment_key = ndb.Key(MpesaPayment, response_json['ConversationID'])
        new_mpesa_payment = MpesaPayment.get_or_insert(new_mpesa_payment_key.id())
        new_mpesa_payment.populate(
            order_id="3001575",
            user_id="3001575",
            phone_no="254723001575",
            merchant_request_id=response_json['OriginatorCoversationID'],
            amount=575
        )
        new_mpesa_payment.put()

    return Response(response.text, status=response.status_code, mimetype='application/json')


@mpesa_push_api.route('/payments/mpesa/payment/push/<string:order_id>', methods=['POST'])
def request_payment_via_mpesa_stk_push(order_id):
    """Used to make an STK PUSH to the user's phone"""
    daraja_stk_push_endpoint = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    order_key = ndb.Key(urlsafe=order_id)
    # order = Order.get_by_id(order_key.string_id())
    order = order_key.get()

    access_token = request.headers['Authorization']
    headers = {
        # "Host": "api.safaricom.co.ke",
        # "Content-Type": "application/json",
        "User-Agent": chrome_browser_user_agent,
        "Authorization": "Bearer {access_token}".format(access_token=access_token),
    }

    timestamp = time.strftime("%Y%m%d%H%M%S")
    base64_encoded_password = base64.b64encode("".join([
        os.environ.get("MPESA_PAYBILL_NUMBER"),
        os.environ.get("MPESA_PAYBILL_PASSKEY"),
        timestamp
    ]))

    user = order.user.get()
    account_reference = str(order_key.integer_id())
    account_ref_str_len = len(account_reference) - 1
    payload = {
        "BusinessShortCode": os.environ.get("MPESA_PAYBILL_NUMBER"),
        # This is generated by base64 encoding BusinessShortcode, Passkey and Timestamp"
        "Password": base64_encoded_password,
        "Timestamp": timestamp,  # format yyyymmddhhiiss",
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(int(round(order.local_overall_cost))),
        # "PartyA": '254723001575',
        "PartyA": user.phone_number,
        "PartyB": os.environ.get("MPESA_PAYBILL_NUMBER"),
        # "PhoneNumber": '254723001575',
        "PhoneNumber": user.phone_number,
        "CallBackURL": "https://{application_id}.appspot.com/payments/mpesa/payment/complete".format(
            application_id=os.environ.get("APPENGINE_SERVER")
        ),
        # "AccountReference": str(order_id),
        "AccountReference": "...{}".format(
            account_reference[account_ref_str_len / 2: account_ref_str_len]
        ),
        "TransactionDesc": "payment for order"
    }

    # Expect this, for a successful push request
    # {
    #     "CheckoutRequestID": "ws_CO_DMZ_105178180_23102018082038007",
    #     "CustomerMessage": "Success. Request accepted for processing",
    #     "MerchantRequestID": "11138-7024993-1",
    #     "ResponseCode": "0",
    #     "ResponseDescription": "Success. Request accepted for processing"
    # }

    # Current working option to make the mpesa stk push request
    # response = urlfetch.fetch(
    #     method=urlfetch.POST,
    #     url=daraja_stk_push_endpoint,
    #     # payload=urllib.urlencode(payload),
    #     payload=json.dumps(payload),
    #     headers=headers
    # )

    session = requests.Session()
    req = requests.Request('POST', daraja_stk_push_endpoint, headers=headers)
    preparedreq = req.prepare()
    # preparedreq = session.prepare_request(req)
    preparedreq.body = json.dumps(payload)
    preparedreq.headers['Content-Type'] = 'application/json'
    response = session.send(preparedreq)
    # response = requests.post(daraja_stk_push_endpoint, data=json.dumps(payload), headers=headers)
    # response.raise_for_status()

    logging.debug("PAYMENT payload: {}".format(json.dumps(payload)))
    logging.debug("PAYMENT request headers: {}".format(response.headers))

    if response.status_code == 200:
        mpesa_push_api_meta_data = response.json() \
            if hasattr(response, 'json') and callable(response.json)\
            else json.loads(response.content)

        new_mpesa_payment_key = ndb.Key(MpesaPayment, mpesa_push_api_meta_data['CheckoutRequestID'])
        new_mpesa_payment = MpesaPayment.get_or_insert(new_mpesa_payment_key.id())

        mpesa_payment_details = {
            "order_id": str(order_key.integer_id()),
            "user_id": user.key.string_id(),
            "phone_no": user.phone_number,
            "merchant_request_id": mpesa_push_api_meta_data['MerchantRequestID'],
            "amount": order.local_overall_cost,
        }
        new_mpesa_payment.populate(**mpesa_payment_details)

        # save the mpesa payment and add the key to the order
        order.mpesa_payment = new_mpesa_payment.put()
        order.put()

        map(lambda attr: mpesa_push_api_meta_data.pop(attr), [
            'ResponseDescription',
            'CustomerMessage',
            # 'CheckoutRequestID'
        ])

        # This is still the 'CheckoutRequestID'
        mpesa_payment_details["payment_id"] = new_mpesa_payment.key.id()
        mpesa_payment_details["daraja_response"] = mpesa_push_api_meta_data
        mpesa_payment_details.pop('merchant_request_id')

        payload = json.dumps(mpesa_payment_details)
        return Response(payload, status=response.status_code, mimetype='application/json')

    # Back proof the response object, incase we decide to switch back to requests lib
    if hasattr(response, 'raise_for_status') and callable(response.raise_for_status):
        setattr(response, 'content', response.text)

    # if response.content is JSON, try decode it
    try:
        response.content = json.loads(response.content)
    except ValueError:
        pass

    error_payload = json.dumps({
        "status_code": response.status_code,
        "daraja_error": response.content,
        "payload_sent": payload
    })
    return Response(error_payload, status=response.status_code, mimetype='application/json')


def get_from(data, name_of_property):
    """Helper array filter function"""
    data = [x['Value'] for x in data if x['Name'] == name_of_property]
    return data[0] if len(data) > 0 else None


def sync_mpesa_payment_details_to_firebase(payment_details):
    firebase_endpoint = 'https://{application_id}.firebaseio.com'.format(
        application_id=os.environ.get("APPENGINE_SERVER")
    )
    firebase_resource = "{firebase_endpoint}/payments/mpesa/{order_id}.json".format(
        firebase_endpoint=firebase_endpoint,
        order_id=payment_details['mpesa_acc']
    )
    firebase_response = requests.post(firebase_resource, data=json.dumps(payment_details))

    if firebase_response.status_code == 200:
        print firebase_response.text
        logging.debug("MPesa payment details synced to FIREBASE: {}".format(
            json.dumps(payment_details)
        ))


@mpesa_push_api.route('/payments/mpesa/payment/complete', methods=['GET', 'POST'])
def payment_completed_webhook():
    """The callback called by the Safaricom Daraja API when the user completes a payment"""
    payment_info = request.get_json() if request.is_json is True else None
    logging.debug('CALLBACK RESPONSE FROM DARAJA: {}'.format(payment_info))
    # logging.debug(request.json)

    if payment_info is not None:

        payment_info = payment_info['Body']['stkCallback']
        payment_key = ndb.Key(MpesaPayment, payment_info['CheckoutRequestID'])
        completed_mpesa_payment = MpesaPayment.get_by_id(payment_key.id())

        # The user cancelled the payment requested
        if payment_info['ResultCode'] is 1032:
            # Expect this response when the user cancels or fails
            # to complete the requested push request
            # {
            #     'Body': {
            #         'stkCallback': {
            #             'CheckoutRequestID': 'ws_CO_DMZ_192558880_27112018175237139',
            #             'ResultCode': 1032,
            #             'MerchantRequestID': '32412-2959058-2',
            #             'ResultDesc': '[STK_CB - ]Request cancelled by user'
            #         }
            #     }
            # }
            pass

        if payment_info['ResultCode'] is not 1032 and 'CallbackMetadata' in payment_info:
            payment_metadata = payment_info['CallbackMetadata']['Item']
            logging.debug(json.dumps(request.json))

            user_phone_no = get_from(payment_metadata, "PhoneNumber")
            mpesa_payment = {
                "amount": get_from(payment_metadata, "Amount"),
                "phone_no": user_phone_no if type(user_phone_no) is str else str(user_phone_no),
                "code": get_from(payment_metadata, "MpesaReceiptNumber"),
            }
            logging.debug(json.dumps(mpesa_payment))

            completed_mpesa_payment.populate(**mpesa_payment)
            completed_mpesa_payment.put()

            # forward teh payment to Vitumob hostgator servers
            timestamp_as_string = get_from(payment_metadata, "TransactionDate")
            datetime_parsed = datetime.strptime(str(timestamp_as_string), '%Y%m%d%H%M%S')
            payload = {
                "id": payment_key.id(),
                "orig": "MPESA",
                "dest": os.environ.get("MPESA_PAYBILL_NUMBER"),
                "tstamp": datetime_parsed.strftime("%Y-%m-%d+%H:%M:%S"),
                "text": json.dumps(payment_info),
                # "customer_id": completed_mpesa_payment.user_id,
                "user": completed_mpesa_payment.phone_no \
                        if completed_mpesa_payment.user_id is None\
                        else completed_mpesa_payment.user_id,
                "pass": base64.b64encode(time.strftime("%Y%m%d%H%M%S")),
                "routemethod_id": 2,
                "routemethod_name": "HTTP",
                "mpesa_code": completed_mpesa_payment.code,
                "mpesa_acc": completed_mpesa_payment.order_id,
                "mpesa_msisdn": completed_mpesa_payment.phone_no,
                "mpesa_trx_date": datetime_parsed.strftime("%d/%m/%Y"),
                "mpesa_trx_time": datetime_parsed.strftime("%I:%M+%p"),
                "mpesa_amt": completed_mpesa_payment.amount,
                "mpesa_sender": completed_mpesa_payment.phone_no,
                "business_number": os.environ.get("MPESA_PAYBILL_NUMBER"),
                # Missing - dest, text, customer_id, pass, mpesa_trx_date, mpesa_trx_time
            }
            logging.debug("Hostagator to recieve this: {}".format(json.dumps(payload)))

            deferred.defer(sync_mpesa_payment_details_to_firebase, payload)

            response = requests.get("https://vitumob.com/mpesa", params=payload)
            if response.status_code == 200:
                return Response(
                    json.dumps(payload),
                    status=response.status_code,
                    mimetype='application/json'
                )

            return Response(response.text, status=response.status_code, mimetype='application/json')

    logging.debug('JSON response from Daraja: {}'.format(request.data))
    return Response('{}', status=200, mimetype='application/json')
