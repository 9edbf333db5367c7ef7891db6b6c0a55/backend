from google.appengine.ext import ndb
from .item import Item
from .coupon import Coupon
from .paypal import PayPalPayment
from .mpesa import MpesaPayment
from .location import Location
from .user import User
from mongoengine import *

class Order(Document):
    user = StringField(kind=User)
    merchant = StringField()
    items = StringField(kind=Item, repeated=True)
    total_cost = FloatField(default=0.00)
    shipping_cost = FloatField(default=0.00)
    waived_shipping_cost = FloatField(default=0.00)
    customs = FloatField(default=0.00)
    vat = FloatField(default=0.00)
    overall_cost = FloatField(default=0.00)
    local_overall_cost = FloatField(default=0.00)
    amount_paid = FloatField(default=0.00)
    balance = FloatField(default=0.00)
    markup = FloatField(default=0.00)
    exchange_rate = FloatField(default=0.00)
    base_currency = StringField(default='USD')
    coupon_code = StringField(kind=Coupon)
    # coupon_code = ndb.ReferenceProperty(Coupon, collection_name='coupon')
    paypal_payment = StringField(kind=PayPalPayment)
    mpesa_payment = StringField(kind=MpesaPayment)
    delivery_location = StringField(kind=Location)

    is_temporary = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    # def _pre_put_hook(self):
    #     self.total_cost = round(self.total_cost, 2)
    #     self.shipping_cost = round(self.shipping_cost, 2)

    #     # If the total cost of items is more than $800 shipping cost is completely waved
    #     if self.total_cost >= 800:
    #         self.waived_shipping_cost = self.shipping_cost
    #         self.shipping_cost = 0.00

    #     self.overall_cost = reduce(lambda a, b: a + b, [
    #         self.total_cost,
    #         self.shipping_cost,
    #         self.customs,
    #         self.vat
    #     ], 0.00)
    #     self.overall_cost = round(self.overall_cost, 2)
    #     self.local_overall_cost = self.overall_cost * self.exchange_rate
    #     self.markup = round((self.overall_cost / self.total_cost) - 1, 2)
    #     # self.markup = float(format(self.markup, ".2f")) * 100
