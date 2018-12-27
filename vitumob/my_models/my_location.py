from mongoengine import *

class Location(Document):
    place_id = StringField()
    name = StringField()
    vicinity = StringField()
    lat = StringField(default=0.00)
    long = StringField(default=0.00)
