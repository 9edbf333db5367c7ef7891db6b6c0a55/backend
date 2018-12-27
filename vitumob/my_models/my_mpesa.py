import time
from datetime import datetime
from mongoengine import *

class MpesaDarajaAccessToken(Document):
    access_token = StringField(default='', required=True)
    expires_in = IntField(default=0, required=True)
    expiring_time = FloatField(default=0.00)
    updated_at = DateTimeField(auto_now=True)

    def _pre_put_hook(self):
        time_now_in_seconds = time.mktime(datetime.now().timetuple())
        self.expiring_time = time_now_in_seconds + self.expires_in

class MpesaPayment(Document):
     # id = ndb.GenericProperty()
    order_id = StringField(default='', required=True)
    user_id = StringField(default='', required=True)
    code = StringField(default='', required=True)
    phone_no = StringField(default='', required=True)
    # checkout_request_id = ndb.StringProperty(default='')
    merchant_request_id = StringField(default='')
    sender = StringField(default='')
    # recoded_trx_date_time = ndb.DateTimeProperty()
    amount = FloatField(default=0.00)
    # transaction_date = ndb.IntegerProperty(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
