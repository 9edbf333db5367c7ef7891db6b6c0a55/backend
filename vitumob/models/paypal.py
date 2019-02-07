# import time
# from datetime import datetime
# from google.appengine.ext import ndb


# class PayPalToken(ndb.Model):
#     app_id = ndb.StringProperty(default='', required=True)
#     access_token = ndb.StringProperty(default='', required=True)
#     expires_in = ndb.IntegerProperty(default=0, required=True)
#     nonce = ndb.StringProperty(default='', required=True)
#     scope = ndb.StringProperty(default='', required=True)
#     token_type = ndb.StringProperty(default='', required=True)
#     updated_at = ndb.DateTimeProperty(auto_now=True)
#     expiring_time = ndb.FloatProperty(default=0.00)

#     def _pre_put_hook(self):
#         self.expiring_time = time.mktime(datetime.now().timetuple()) + self.expires_in


# class PayPalPayer(ndb.Model):
#     # id = ndb.StringProperty(required=True)
#     email = ndb.StringProperty(required=True)
#     first_name = ndb.StringProperty()
#     last_name = ndb.StringProperty()
#     payment_method = ndb.StringProperty(required=True)


# class PayPalPayment(ndb.Model):
#     # id = ndb.StringProperty(required=True)
#     amount = ndb.FloatProperty(required=True, default=0.00)
#     local_amount = ndb.FloatProperty(default=0.00)
#     client = ndb.StructuredProperty(PayPalPayer)
#     create_time = ndb.DateTimeProperty()
#     completed = ndb.BooleanProperty(default=True)
#     created_at = ndb.DateTimeProperty(auto_now_add=True)
#     updated_at = ndb.DateTimeProperty(auto_now=True)




import time
from datetime import datetime
from mongoengine import *

class PayPalToken(EmbeddedDocument):
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


class PayPalPayment(Document):
    # id = ndb.StringProperty(required=True)
    amount = FloatField(required=True, default=0.00)
    local_amount = FloatField(default=0.00)
    client = ndb.StructuredProperty(PayPalPayer)
    create_time = DateTimeField()
    completed = BooleanField()(default=True)
    created_at = DateTimeField()(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)