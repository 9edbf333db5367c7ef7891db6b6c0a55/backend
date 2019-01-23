from google.appengine.ext import ndb


class Coupon(ndb.Model):
    code = ndb.StringProperty()
    percent = ndb.FloatProperty(default=0.00)
    amount = ndb.FloatProperty(default=0.00)
    multiple_use = ndb.BooleanProperty(default=False)
    used = ndb.IntegerProperty(default=0)
    expiration_date = ndb.DateTimeProperty(auto_now_add=True)
    comment = ndb.StringProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

