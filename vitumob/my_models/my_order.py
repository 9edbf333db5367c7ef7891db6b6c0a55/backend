from mongoengine import *

from .my_item import Item
from .my_coupon import Coupon
from .my_paypal import PayPalPayment
from .my_mpesa import MpesaPayment
from .my_location import Location
from .my_user import User

class Order(Document):
    user = KeyField(kind=User)
    merchant = StringField()
    items = KeyField(kind=Item, repeated=True)
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
    coupon_code = KeyField(kind=Coupon)

    paypal_payment = KeyField(kind=PayPalPayment)
    mpesa_payment = KeyField(kind=MpesaPayment)
    delivery_location = KeyField(kind=Location)

    is_temporary = BooleanField(default=True)
    created_at = DateTimeFieldField(auto_now_add=True)
    updated_at = DateTimeFieldField(auto_now=True)