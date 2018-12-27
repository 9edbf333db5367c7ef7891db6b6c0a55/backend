import time
from datetime import datetime
from mongoengine import *

class PayPalToken(Document):
    app_id = StringField(default='', required=True)
    access_token = StringField(default='', required=True)
    expires_in = IntField(default=0, required=True)
    nonce = StringField(default='', required=True)
    scope = StringField(default='', required=True)
    token_type = StringField(default='', required=True)
    updated_at = DateTimeField(auto_now=True)
    expiring_time = FloatField(default=0.00)