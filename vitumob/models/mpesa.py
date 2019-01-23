import time
from datetime import datetime
from google.appengine.ext import ndb


class MpesaDarajaAccessToken(ndb.Expando):
    access_token = ndb.StringProperty(default='', required=True)
    expires_in = ndb.IntegerProperty(default=0, required=True)
    expiring_time = ndb.FloatProperty(default=0.00)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def _pre_put_hook(self):
        time_now_in_seconds = time.mktime(datetime.now().timetuple())
        self.expiring_time = time_now_in_seconds + self.expires_in


class MpesaPayment(ndb.Expando):
    # id = ndb.GenericProperty()
    order_id = ndb.StringProperty(default='', required=True)
    user_id = ndb.StringProperty(default='', required=True)
    code = ndb.StringProperty(default='', required=True)
    phone_no = ndb.StringProperty(default='', required=True)
    # checkout_request_id = ndb.StringProperty(default='')
    merchant_request_id = ndb.StringProperty(default='')
    sender = ndb.StringProperty(default='')
    # recoded_trx_date_time = ndb.DateTimeProperty()
    amount = ndb.FloatProperty(default=0.00)
    # transaction_date = ndb.IntegerProperty(default=0)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
