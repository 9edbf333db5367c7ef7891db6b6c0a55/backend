from mongoengine import *
from datetime import datetime

class Currency(EmbeddedDocument):
    code = StringField(required=True)
    rate = FloatField(default=0.00, required=True)

class Rates(Document):
    api_id = StringField(primary_key=True)
    rates = ListField(EmbeddedDocumentField(Currency, repeated=True))
    base = StringField(default='USD')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(default=datetime.now())
