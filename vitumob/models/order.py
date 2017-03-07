from google.appengine.ext import ndb
from .item import Item


class Order(ndb.Expando):
    uuid = ndb.StringProperty()
    # belongs_to = ndb.StringProperty()
    merchant = ndb.StringProperty()
    items = ndb.KeyProperty(kind=Item, repeated=True)
    total_cost = ndb.FloatProperty(default=0.00)
    shipping_cost = ndb.FloatProperty(default=0.00)
    customs = ndb.ComputedProperty(lambda self: self.total_cost * 0.12)
    vat = ndb.ComputedProperty(lambda self: self.total_cost * 0.16)
    overall_cost = ndb.FloatProperty()
    markup = ndb.FloatProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def _pre_put_hook(self):
        self.overall_cost = reduce(lambda a, b: a + b, [
            self.total_cost,
            self.shipping_cost,
            self.customs,
            self.vat
        ], 0.00)

        self.markup = (self.overall_cost / self.total_cost) - 1
        self.markup = float(format(self.markup, ".4f")) * 100
