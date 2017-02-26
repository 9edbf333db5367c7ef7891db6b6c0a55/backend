from google.appengine.ext import ndb
from .item import Item


class Order(ndb.Model):
    uuid = ndb.StringProperty()
    # belongs_to = ndb.StringProperty()
    merchant = ndb.StringProperty()
    items = ndb.KeyProperty(kind=Item, repeated=True)
    total_cost = ndb.FloatProperty(default=0.00)
    shipping_cost = ndb.FloatProperty(default=0.00)
    overall_cost = ndb.ComputedProperty(lambda self: self.total_cost + self.shipping_cost)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
