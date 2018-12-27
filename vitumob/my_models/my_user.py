from mongoengine import *
from .my_location import Location

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