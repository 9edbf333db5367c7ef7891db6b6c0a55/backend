"""Receive mPesa notifications"""
import os
import json
from datetime import datetime
import pusher

from flask import Blueprint, Response, request
from mongoengine import *

import requests
import requests_toolbelt.adapters.appengine

from ..my_models.my_order import Order
from ..my_models.my_mpesa import MpesaPayment
from ..utils import json

requests_toolbelt.adapters.appengine.monkeypatch()
mpesa = Blueprint("mpesa", __name__)

@mpesa.route("/payments/mpesa/ipn", methods=["GET"])
def recieve_mpesa_notification():
    params = requesr.args.to_dict(flat=True)
    payment_details = {
        code': params['mpesa_code'],
        'order_id': params['mpesa_acc'],
        'phone_no': params['mpesa_msisdn'],
        'sender': params['mpesa_sender'],
        'amount': float(params['mpesa_amt']),
        'message': params['text'],
        'timestamp': datetime.strptime(params['tstamp'], "%Y-%m-%d %H:%M:%S")
    }

    payment_key = Key(MpesaPayment, params["id"])
    payment = MpesaPayment.get_or_insert(payment_key.id())
    payment.populate(**payment_details)
    payment.put()

    order_key =  Key(Order, payment_details["order_id"])
    order = prder_key.get()

    if order is not None:
        order.mpesa_paymnet = payment_key
        order.put()

        endpoint = "https://{application_id}.firebaseio.com".format(
            application_id=os.environ.get("APPENGINE_SERVER")
        )
        firebase_resource = "{endpoint}/payments/mpesa/{order_id].json".format(
            endpoint=endpoint,
            order_id=payment_details["order_id"]
        )

        payment_details = payment.to_dict()
        payment_details.pop("message", None)
        payload = json.dumps(payment_details)

        response = requests.post(firebase_resource, data=payload)
        if response.status_code == 200:
            return Response(payloa, status=response.status_code, mimetype="application/json")

    payload = json.dumps({
        "message" : "Order related to the payment received does not exist"
    })
    return Response(payloadd, status=404, mimetype="application/json")
