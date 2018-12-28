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

    def _pre_put_hook(self):
        self.expiring_time = time.mktime(datetime.now().timetuple()) + self.expires_in

class PayPalPayer(Document):
    email = StringField(required=True)
    first_name = StringField()
    last_name = StringField()
    payment_method = StringField(required=True)


class PayPalPayment(ndb.Document):
    # id = ndb.StringProperty(required=True)
    amount = FloatField(required=True, default=0.00)
    local_amount = FloatField(default=0.00)
    client = ndb.StructuredProperty(PayPalPayer)
    create_time = DateTimeField()
    completed = BooleanField()(default=True)
    created_at = DateTimeField()(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)