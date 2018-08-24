from google.appengine.ext import ndb
from .item import Item
from .coupon import Coupon
from .paypal import PayPalPayment
from .mpesa import MpesaPayment
from .location import Location
from .user import User


class Order(ndb.Expando):
    user = ndb.KeyProperty(kind=User)
    merchant = ndb.StringProperty()
    items = ndb.KeyProperty(kind=Item, repeated=True)
    total_cost = ndb.FloatProperty(default=0.00)
    shipping_cost = ndb.FloatProperty(default=0.00)
    waived_shipping_cost = ndb.FloatProperty(default=0.00)
    customs = ndb.FloatProperty(default=0.00)
    vat = ndb.FloatProperty(default=0.00)
    overall_cost = ndb.FloatProperty(default=0.00)
    local_overall_cost = ndb.FloatProperty(default=0.00)
    amount_paid = ndb.FloatProperty(default=0.00)
    balance = ndb.FloatProperty(default=0.00)
    markup = ndb.FloatProperty(default=0.00)
    exchange_rate = ndb.FloatProperty(default=0.00)
    base_currency = ndb.StringProperty(default='USD')
    coupon_code = ndb.KeyProperty(kind=Coupon)
    # coupon_code = ndb.ReferenceProperty(Coupon, collection_name='coupon')
    paypal_payment = ndb.KeyProperty(kind=PayPalPayment)
    mpesa_payment = ndb.KeyProperty(kind=MpesaPayment)
    delivery_location = ndb.KeyProperty(kind=Location)

    is_temporary = ndb.BooleanProperty(default=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

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
