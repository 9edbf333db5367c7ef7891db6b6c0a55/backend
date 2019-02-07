# from google.appengine.ext import ndb


# class Coupon(ndb.Model):
#     code = ndb.StringProperty()
#     percent = ndb.FloatProperty(default=0.00)
#     amount = ndb.FloatProperty(default=0.00)
#     multiple_use = ndb.BooleanProperty(default=False)
#     used = ndb.IntegerProperty(default=0)
#     expiration_date = ndb.DateTimeProperty(auto_now_add=True)
#     comment = ndb.StringProperty()
#     created_at = ndb.DateTimeProperty(auto_now_add=True)
#     updated_at = ndb.DateTimeProperty(auto_now=True)


# from vitumob import models
from mongoengine import *
from datetime import datetime

class Coupon(Document):
    coupon_id = StringField(primary_key=True)
    code = StringField()
    percent = FloatField(default=0.00)
    amount = FloatField(default=0.00)
    multiple_use = BooleanField(default=False)
    used = IntField(default=0)
    expiration_date = DateTimeField(auto_now_add=True)
    comment = StringField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
