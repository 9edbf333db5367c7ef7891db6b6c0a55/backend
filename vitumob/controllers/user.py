"""User persistance done here"""

import json

from flask import Blueprint, Response, request
from google.appengine.ext import ndb

from ..models.user import User


user = Blueprint('user', __name__)


@user.route('/user', methods=['POST'])
def create_user():
    """Add/create a new user"""
    new_user = json.loads(request.json['user'])

    user = User.get_by_id(ndb.Key(User, new_user['id']).id())
    if user is None:
        user = User(**new_user)
        user_key = user.put()
        payload = json.dumps({ 'user_id': user_key.id() })
        return Response(payload, status=200, mimetype='application/json')

    payload = json.dumps({
        'message': 'error/user-exists:userid={id}'.format(id=user.key.id()),
    })
    return Response(payload, status=409, mimetype='application/json')


@user.route('/user/<string:user_id>', methods=['PUT', 'PATCH'])
def update_user(user_id):
    """Update user's credentials"""
    user_updates = json.loads(request.json['user'])

    user = User.get_by_id(ndb.Key(User, user_id).id())
    if user is not None:
        (user_updates.pop('id', None) if 'id' in user_updates else None)
        user.populate(**user_updates)
        user.put()
        return Response(json.dumps({}), status=200, mimetype='application/json')

    payload = json.dumps({
        'message': 'error/user-not-found',
    })
    return Response(payload, status=404, mimetype='application/json')
