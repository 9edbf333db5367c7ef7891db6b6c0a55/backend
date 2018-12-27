from mongoengine import *


class Currency(Document):
    code = StringField(required=True)
    rate = FloatField(default=0.00, required=True)


class Rates(Document):
    # rates = StructuredField(Currency, repeated=True)
    base = StringField(default='USD')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

# change line 10