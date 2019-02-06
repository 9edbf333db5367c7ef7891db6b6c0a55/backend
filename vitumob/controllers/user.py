"""User persistance done here"""

import os
import json
import logging

from datetime import datetime
from flask import Blueprint, Response, request
# from google.appengine.api import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext import ndb

import requests
import requests_toolbelt.adapters.appengine

from ..models.user import User
from ..utils import ndb_json


requests_toolbelt.adapters.appengine.monkeypatch()

user = Blueprint('user', __name__)
endpoint = os.environ.get("HOSTGATOR_SYNC_ENDPOINT")


@user.route('/user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    """Get the user with the specified `user_id`"""
    user = ndb.Key(User, user_id).get()
    user_payload = user.to_dict()
    user_payload['id'] = user.key.id()
    payload = ndb_json.dumps(user_payload)
    return Response(payload, status=200, mimetype='application/json')


# deferred function
def sync_user_to_hostgator_server(endpoint, user_key, updating=False):
    """Sync a new user & any updates of the user info to the Hostgator server"""
    user = user_key.get()
    user_payload = user.to_dict()
    user_payload['id'] = user.key.id()

    payload = ndb_json.dumps({
        'user': user_payload,
    })
    logging.info("Payload: {}".format(payload))

    rest_uri = '{endpoint}/user' if updating is False else '{endpoint}/user/{user_id}'
    resource = rest_uri.format(endpoint=endpoint, user_id=user.key.id())

    response = requests.post(resource, data=payload) \
        if updating is False else requests.put(resource, data=payload)

    logging.info("Response Status Code: {status_code}, Response Body: {body}".format(
        status_code=response.status_code,
        body=response.text
    ))


@user.route('/user', methods=['POST'])
def create_user():
    """Add/create a new user"""
    new_user = json.loads(request.json['user'])

    user = ndb.Key(User, new_user['id']).get()
    if user is None:
        user = User(**new_user)
        user_key = user.put()

        deferred.defer(sync_user_to_hostgator_server, endpoint, user_key)

        payload = json.dumps({'user_id': user.key.id()})
        return Response(payload, status=200, mimetype='application/json')

    payload = json.dumps({
        'message': "error/user-exists:userid={id}".format(id=user.key.id()),
    })
    return Response(payload, status=409, mimetype='application/json')


@user.route('/user/<string:user_id>', methods=['PUT', 'PATCH'])
def update_user(user_id):
    """Update user's credentials"""
    user_updates = json.loads(request.json['user'])

    user = ndb.Key(User, user_id).get()
    if user is not None:
        if 'id' in user_updates:
            user_updates.pop('id', None)

        user.populate(**user_updates)
        user_key = user.put()

        deferred.defer(sync_user_to_hostgator_server, endpoint, user_key, True)

        timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now())
        payload = json.dumps({'timestamp': timestamp})
        return Response(payload, status=200, mimetype='application/json')

    payload = json.dumps({
        'message': 'error/user-not-found',
    })
    return Response(payload, status=404, mimetype='application/json')
