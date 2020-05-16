# package imports
from mongoengine import Document
from mongoengine.fields import DateTimeField, ReferenceField, StringField, DecimalField, BooleanField
from datetime import datetime
import graphene


class Stock(Document):
    meta = {'collection': 'stocks'}
    ID = StringField(default=None)
    ticker = StringField(required=True, primary_key=True)
    last_updated = DateTimeField(default=datetime.now)

class Option(Document):
    meta = {'collection': 'options'}

    ID = StringField(required=True, primary_key=True)
    ticker = StringField(required=True)
    type = StringField(required=True, choices=['CALL', 'PUT'])

    implied_vol = DecimalField()
    implied_vol_rank = DecimalField()
    delta = DecimalField()
    theta = DecimalField()
    vega = DecimalField()

    current_value = DecimalField()
    # also track previous current_values from the same trading day?
    theoretical_value = DecimalField()
    # also track previous current_values from the same trading day?

    #underlying = ReferenceField(Stock, required=True)
    #strike = DecimalField(required=True)
    #expiry = DateTimeField(required=True)
    last_updated = DateTimeField(default=datetime.now)

class Value():
    # any other options aside from document?
    pass
