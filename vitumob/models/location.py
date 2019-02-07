# from google.appengine.ext import ndb


# class Location(ndb.Model):
#     # id = ndb.StringProperty() set on
#     place_id = ndb.StringProperty()
#     name = ndb.StringProperty()
#     vicinity = ndb.StringProperty()
#     lat = ndb.FloatProperty(default=0.00)
#     long = ndb.FloatProperty(default=0.00)


from flask_mongoengine import MongoEngine

class Location(Document):
    place_id = StringField()
    name = StringField()
    vicinity = StringField()
    lat = StringField(default=0.00)
    long = StringField(default=0.00)
