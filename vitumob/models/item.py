from google.appengine.ext import ndb


class ShippingInfo(ndb.Expando):
    length = ndb.FloatProperty()
    height = ndb.FloatProperty()
    width = ndb.FloatProperty()
    weight = ndb.FloatProperty()
    shipping_cost = ndb.FloatProperty()
    is_prime_item = ndb.BooleanProperty()


class Item(ndb.Expando):
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    image = ndb.StringProperty()
    link = ndb.StringProperty()
    quantity = ndb.IntegerProperty()
    price = ndb.FloatProperty()
    shipping_info = ndb.StructuredProperty(ShippingInfo)
    total_cost = ndb.FloatProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
    # Others - size, color, asin, model_no
