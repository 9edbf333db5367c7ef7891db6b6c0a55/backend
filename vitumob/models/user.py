# from google.appengine.ext import ndb
# from .location import Location


# class FacebookCredentials(ndb.Model):
#     # id = ndb.StringProperty()
#     gender = ndb.StringProperty()
#     profile_photo = ndb.StringProperty()
#     age_range = ndb.IntegerProperty()
#     birthday = ndb.StringProperty()
#     location = ndb.StringProperty()
#     access_token = ndb.StringProperty()


# class User(ndb.Expando):
#     # id = ndb.StringProperty(required=True)
#     email = ndb.StringProperty(required=True)
#     email_verified = ndb.BooleanProperty(default=False)
#     device_uuid = ndb.StringProperty()
#     name = ndb.StringProperty()
#     phone_number = ndb.StringProperty()
#     delivery_location = ndb.KeyProperty(kind=Location)
#     facebook_credentials = ndb.StructuredProperty(FacebookCredentials)
#     created_at = ndb.DateTimeProperty(auto_now_add=True)
#     updated_at = ndb.DateTimeProperty(auto_now=True)




from flask_mongoengine import MongoEngine
from pymongo import MongoClient
from google.appengine.ext import ndb
from .location import Location

class FacebookCredentials(Document):
    gender = StringField()
    profile_photo = StringField()
    age_range = IntField()
    birthday = StringField()
    location = StringField()
    access_token = StringField()

class User(Document):
    # id = ndb.StringProperty(required=True)
    email = StringField(required=True)
    email_verified = BooleanField(default=False)
    device_uuid = StringField()
    name = StringField()
    phone_number = StringField()
    delivery_location = KeyField(kind=Location)
    # facebook_credentials = StructuredField(FacebookCredentials)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

# change line 20