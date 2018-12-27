# from vitumob import models
from mongoengine import *

class Coupon(Document):
    code = StringField()
    percent = FloatField(default=0.00)
    amount = FloatField(default=0.00)
    multiple_use = BooleanField(default=False)
    used = IntField(default=0)
    expiration_date = DateTimeField(auto_now_add=True)
    comment = StringField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
