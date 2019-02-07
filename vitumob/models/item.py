# from google.appengine.ext import ndb


# class ShippingInfo(ndb.Model):
#     length = ndb.FloatProperty()
#     height = ndb.FloatProperty()
#     width = ndb.FloatProperty()
#     weight = ndb.FloatProperty()
#     shipping_cost = ndb.FloatProperty(default=0.00)
#     local_cost = ndb.FloatProperty(default=0.00)
#     is_prime_item = ndb.BooleanProperty()


# class Item(ndb.Expando):
#     item_id = ndb.GenericProperty()
#     name = ndb.StringProperty()
#     image = ndb.StringProperty()
#     link = ndb.StringProperty()
#     quantity = ndb.IntegerProperty(default=1)
#     price = ndb.FloatProperty(default=0.00)
#     local_price = ndb.FloatProperty(default=0.00)
#     total_cost = ndb.FloatProperty(default=0.00)
#     shipping_cost = ndb.FloatProperty(default=0.00)
#     overall_cost = ndb.ComputedProperty(lambda self: self.total_cost + self.shipping_cost)
#     shipping_info = ndb.StructuredProperty(ShippingInfo)
#     created_at = ndb.DateTimeProperty(auto_now_add=True)
#     updated_at = ndb.DateTimeProperty(auto_now=True)
#     # Others - size, color, asin, model_no

#     def _pre_put_hook(self):
#         self.item_id = str(self.item_id)
#         self.total_cost = self.local_price * self.quantity


# from pymongo import MongoClient
from flask_mongoengine import MongoEngine

class ShippingIngo(Document):
    length = FloatField()
    height = FloatField()
    width = FloatField()
    weight = FloatField()
    shipping_cost = FloatField(default=0.00)
    local_cost = FloatField(default=0.00)
    is_prime_item = BooleanField()

class Item(Document):
    item_id = GenericReferenceField()
    name = StringField()
    image = StringField()
    link = StringField()
    quantity = IntField(default=1)
    price = FloatField(default=0.00)
    local_price = FloatField(default=0.00)
    total_cost = FloatField(default=0.00)
    shipping_cost = FloatField(default=0.00)
    # overall_cost = ComputedField(lambda self: self.total_cost + self.shipping_cost)
    # shipping_info = StructuredField(ShippingInfo)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def _pre_put_hook(self):
        self.item_id = str(self.item_id)
        self.total_cost = self.local_price * self.quantity


# change line 23, 24
# find the equivalence of StructuredField for mongodb