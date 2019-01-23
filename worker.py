"""Tasks that should be executed in the background"""

import os
from flask import Flask, Response, request
from google.appengine.ext import ndb
from mongoengine import *


import requests
import requests_toolbelt.adapters.appengine


requests_toolbelt.adapters.appengine.monkeypatch()

worker = Flask(__name__)
endpoint = os.environ.get("HOSTGATOR_SYNC_ENDPOINT")


@worker.route('/user', methods=['POST'])
def sync_user_to_old_backend():
    """This function will sync a new user data to the old backend"""
    payload = request.form['payload']
    resource = '{endpoint}/user'.format(endpoint=endpoint)
    response = requests.post(resource, data=payload)
    return Response(response.text, status=response.status_code, mimetype='application/json')
    # return Response(payload, status=200, mimetype='application/json')


@worker.route('/user/<string:user_id>', methods=['PUT'])
def update_user_info_in_old_backend(user_id):
    """This function will update the user in with the ID provided data to the old backend"""
    payload = request.form['payload']
    resource = '{endpoint}/user/{user_id}'.format(endpoint=endpoint, user_id=user_id)
    response = requests.put(resource, data=payload)
    return Response(response.text, status=response.status_code, mimetype='application/json')
    # return Response(payload, status=200, mimetype='application/json')


@worker.route('/order/<string:order_id>', methods=['POST'])
def sync_users_order_to_old_backend(order_id):
    """This function will sync the user's requested order to the old backend"""
    order_key = Key(Order, order_id)
    order = order_key.get()

    order_payload = order.to_dict()
    order_payload['id'] = order_key.id()
    order_payload['user_id'] = order.user.get().key.id()
    payload = json.dumps({
        'order': order_payload,
    })
    resource = '{endpoint}/order'.format(endpoint=endpoint)
    response = requests.post(resource, data=payload)
    return Response(response.text, status=response.status_code, mimetype='application/json')
    # return Response(payload, status=200, mimetype='application/json')


@worker.route('/order/<string:order_id>/paypal/payment', methods=['PUT'])
def sync_payment_of_order_to_old_backend(order_id):
    """This function will sync the PayPal payment made by user to the old backend"""
    order_key = Key(Order, order_id)
    order = order_key.get()

    payment = order.paypal_payment.get()
    payment_payload = payment.to_dict()
    payment_payload['id'] = payment.key.id()
    payment_payload['user_id'] = order.user.get().key.id()
    payment_payload['order_id'] = order.key.id()
    payload = ndb_json.dumps({
        'payment': payment_payload,
    })
    resource = '{endpoint}/order/{order_id}/payment'.format(endpoint=endpoint, order_id=order_id)
    response = requests.post(resource, data=payload)
    return Response(response.text, status=response.status_code, mimetype='application/json')
    # return Response(payload, status=200, mimetype='application/json')


if __name__ == '__main__':
    worker.run(host='127.0.0.1', port=8080, debug=True)
