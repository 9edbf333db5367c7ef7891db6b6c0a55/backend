from mongoengine import *
from mongoengine import signals
from datetime import datetime
from mongoengine.queryset import QuerySet


class Currency(EmbeddedDocument):
    code = StringField(required=True)
    rate = FloatField(default=0.00, required=True)

class Rates(Document):
    api_id = StringField(primary_key=True)
    rates = EmbeddedDocumentField(Currency, repeated=True)
    base = StringField(default='USD')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
