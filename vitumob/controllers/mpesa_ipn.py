"""Recieve mPesa notifications"""

import os
import json
from datetime import datetime
import pusher

from flask import Blueprint, Response, request
from google.appengine.ext import ndb

import requests
import requests_toolbelt.adapters.appengine

from ..models.order import Order
from ..models.mpesa import MpesaPayment
from ..utils import ndb_json


requests_toolbelt.adapters.appengine.monkeypatch()
mpesa_ipn = Blueprint('mpesa_ipn', __name__)


@mpesa_ipn.route('/payments/mpesa/ipn', methods=['GET'])
def recieve_mpesa_notification():
    params = request.args.to_dict(flat=True)
    payment_details = {
        'code': params['mpesa_code'],
        'order_id': params['mpesa_acc'],
        'phone_no': params['mpesa_msisdn'],
        'user_name': params['mpesa_sender'],
        'amount': float(params['mpesa_amt']),
        'message': params['text'],
        'timestamp': datetime.strptime(params['tstamp'], "%Y-%m-%d %H:%M:%S")
    }

    payment_key = ndb.Key(MpesaPayment, params['id'])
    payment = MpesaPayment.get_or_insert(payment_key.id())
    payment.populate(**payment_details)
    payment.put()

    order_key = ndb.Key(Order, payment_details['order_id'])
    order = order_key.get()

    if order is not None:
        order.mpesa_payment = payment_key
        order.put()

        endpoint = 'https://{application_id}.firebaseio.com'.format(
            application_id=os.environ.get("APPENGINE_SERVER")
        )
        firebase_resource = "{endpoint}/payments/mpesa/{order_id}.json".format(
            endpoint=endpoint,
            order_id=payment_details['order_id']
        )

        payment_details = payment.to_dict()
        payment_details.pop('message', None)
        payload = ndb_json.dumps(payment_details)

        response = requests.post(firebase_resource, data=payload)
        if response.status_code == 200:
            return Response(payload, status=response.status_code, mimetype='application/json')

    payload = json.dumps({
        'message': 'Order related to the payment recieved does not exist'
    })
    return Response(payload, status=404, mimetype='application/json')
