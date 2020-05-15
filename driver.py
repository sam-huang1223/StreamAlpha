from ib_insync import *

from pymongo import MongoClient

import configparser

config = configparser.ConfigParser()

# config.ini contains sensitive credentials
with open('config.ini') as f:
    config.read_file(f)

MONGODB_ATLAS_PASSWORD = config['MongoDB Atlas']['MONGODB_ATLAS_PASSWORD']

client = MongoClient('mongodb+srv://streamalpha:{password}@streamalpha-o9mip.mongodb.net/test?retryWrites=true&w=majority'.format(password=MONGODB_ATLAS_PASSWORD))

instruments = client.instruments

"""

option = {
    'ticker' : None,  # parent
    'expiry_date' : None,
    'strike' : None,
    'type' : None,
    'implied_vol' : None,
    # greeks
}
instruments.options.insert_one(option)

# store historic data in 

"""

ib = IB()
ib.connect('127.0.0.1', 7496, clientId=1)


"""
scanner_nasdaq = ScannerSubscription(
    instrument='STK', 
    locationCode='STK.NASDAQ', 
    scanCode='HIGH_OPT_IMP_VOLAT')

nasdaq_results = ib.reqScannerData(scanner_nasdaq)

print(f'{len(nasdaq_results)} results, first one:')
print(nasdaq_results[0])
print(nasdaq_results[1])

print()

scanner_nyse = ScannerSubscription(
    instrument='STK', 
    locationCode='STK.NYSE', 
    scanCode='HIGH_OPT_IMP_VOLAT')

nyse_results = ib.reqScannerData(scanner_nyse)

print(f'{len(nyse_results)} results, first one:')
print(nyse_results[0])
print(nyse_results[1])
"""

"""
# can't use ib scanner - results capped at 50 items without market data subscription
# scanner from https://robintrack.net/

stock = Stock('SUPV', '', 'USD')
out = ib.reqContractDetails(stock)

print(out)



chains = ib.reqSecDefOptParams(, '', 'STK', 233587209)

chains = util.df(chains)

# update chain parameters weekly

print(chains)
"""

ib.disconnect()



"""
contract = Forex('EURUSD')
bars = ib.reqHistoricalData(
    contract, endDateTime='', durationStr='30 D',
    barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True)

# convert to pandas dataframe:
df = util.df(bars)
print(df)
"""

"""
option = Option('EOE', '20171215', 490, 'P', 'FTA', multiplier=100)

calc = ib.calculateImpliedVolatility(
    option, optionPrice=6.1, underPrice=525))
print(calc)

calc = ib.calculateOptionPrice(
    option, volatility=0.14, underPrice=525))
print(calc)
"""