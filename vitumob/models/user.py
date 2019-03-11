from google.appengine.ext import ndb
from .location import Location


class FacebookCredentials(ndb.Model):
    # id = ndb.StringProperty()
    gender = ndb.StringProperty()
    profile_photo = ndb.StringProperty()
    age_range = ndb.IntegerProperty()
    birthday = ndb.StringProperty()
    location = ndb.StringProperty()
    access_token = ndb.StringProperty()


class User(ndb.Expando):
    # id = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    email_verified = ndb.BooleanProperty(default=False)
    device_uuid = ndb.StringProperty()
    name = ndb.StringProperty()
    phone_number = ndb.StringProperty()
    delivery_location = ndb.KeyProperty(kind=Location)
    facebook_credentials = ndb.StructuredProperty(FacebookCredentials)
    shipping_only_id = ndb.IntegerProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
