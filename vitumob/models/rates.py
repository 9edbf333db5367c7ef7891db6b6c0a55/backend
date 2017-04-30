from google.appengine.ext import ndb


class Currency(ndb.Model):
    code = ndb.StringProperty(required=True)
    rate = ndb.FloatProperty(default=0.00, required=True)


class Rates(ndb.Model):
    rates = ndb.StructuredProperty(Currency, repeated=True)
    base = ndb.StringProperty(default='USD')
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
