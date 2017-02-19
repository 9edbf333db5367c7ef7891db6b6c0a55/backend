from google.appengine.ext import ndb
from .item import Item

class Order(ndb.Expando):
    name = ndb.StringProperty()
    host = ndb.StringProperty()
    items = ndb.StructuredProperty(Item, repeated=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

# class Order(ndb.Expando):
#     uuid = ndb.StringProperty()
#     location = ndb.StringProperty()
#     amount = ndb.FloatProperty()
#     total = ndb.FloatProperty()
#     exchange_rate = ndb.FloatProperty()
#     customs = ndb.FloatProperty()
#     shipping_cost = ndb.FloatProperty()
#     vat = ndb.FloatProperty()
#     coupon = ndb.StringProperty()
#     items = ndb.StructuredProperty(Item, repeated=True)
#     created_at = ndb.DateTimeProperty(auto_now_add=True)
#     updated_at = ndb.DateTimeProperty(auto_now=True)
