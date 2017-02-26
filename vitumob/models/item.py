from google.appengine.ext import ndb


class ShippingInfo(ndb.Model):
    length = ndb.FloatProperty()
    height = ndb.FloatProperty()
    width = ndb.FloatProperty()
    weight = ndb.FloatProperty()
    shipping_cost = ndb.FloatProperty(default=0.00)
    is_prime_item = ndb.BooleanProperty()


class Item(ndb.Expando):
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    image = ndb.StringProperty()
    link = ndb.StringProperty()
    quantity = ndb.IntegerProperty(default=1)
    price = ndb.FloatProperty(default=0.00)
    total_cost = ndb.FloatProperty(default=0.00)
    shipping_cost = ndb.FloatProperty(default=0.00)
    overall_cost = ndb.ComputedProperty(lambda self: self.total_cost + self.shipping_cost)
    shipping_info = ndb.StructuredProperty(ShippingInfo)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
    # Others - size, color, asin, model_no
