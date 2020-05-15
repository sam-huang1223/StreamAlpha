# package imports
from mongoengine import connect
import configparser

# local imports
from models import Stock

# admin
config = configparser.ConfigParser()
# config.ini contains sensitive credentials
with open('config.ini') as f:
    config.read_file(f)
MONGODB_ATLAS_PASSWORD = config['MongoDB Atlas']['MONGODB_ATLAS_PASSWORD']


def init_db():
    connect('instruments', host='mongodb+srv://streamalpha:{password}@streamalpha-o9mip.mongodb.net/?retryWrites=true&w=majority'.format(password=MONGODB_ATLAS_PASSWORD), alias='default')

    instruments = Stock(ticker='TEST', type='TEST', ID='TEST')
    #instruments.save()
