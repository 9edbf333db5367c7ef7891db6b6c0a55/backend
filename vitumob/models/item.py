from google.appengine.ext import ndb

class Item(ndb.Expando):
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    image = ndb.StringProperty()
    link = ndb.StringProperty()
    quantity = ndb.IntegerProperty()
    price = ndb.FloatProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
    # Others - size, color
