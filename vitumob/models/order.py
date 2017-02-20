from google.appengine.ext import ndb
from .item import Item

class Order(ndb.Model):
    name = ndb.StringProperty()
    host = ndb.StringProperty()
    items = ndb.StructuredProperty(Item, repeated=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
