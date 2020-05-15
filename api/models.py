# package imports
from mongoengine import Document
from mongoengine.fields import DateTimeField, ReferenceField, StringField
from datetime import datetime


class Stock(Document):
    meta = {'collection': 'stocks'}
    ticker = StringField()
    type = StringField()
    ID = StringField()

    # add last updated field