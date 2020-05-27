import ib_insync

import configparser

"""
import requests

r = requests.post("http://localhost:5000/stock/AAL", data={'ID': "1234567"})
print(r.status_code, r.reason)
print(r.text)
"""

class IBKR:
    def __init__(self):
        self._setup()

    def _setup(self):
        # admin
        config = configparser.ConfigParser()

        # config.ini contains sensitive credentials
        with open('config.ini') as f:
            config.read_file(f)
        self.IBKR_FLEXREPORT_TOKEN = str(config['IB API']['IBKR_FLEXREPORT_TOKEN'])


    def query_flexreport(self, queryID, savepath=None):
        """
        The example code begins in a similar fashion to the historical data example; 
        we make one of these weird client objects containing a server wrapper connection, 
        make one of these slightly less weird contract objects (here it is for December 2018 Eurodollar futures), 
        resolve it into a populated contract object (explained more fully here) and then shove that into a request for market data.

        :param a: x
        :param path: specify a path (from root folder) if you want to save the output, defaults to not saving
        :return: x
        """

        ib_insync.util.logToConsole()
        trades = ib_insync.FlexReport(self.IBKR_FLEXREPORT_TOKEN, queryID)
        if savepath:
            trades.save(savepath)
            ib_insync.flexreport._logger.info('Statement has been saved.')

    def play(self):
        report = ib_insync.FlexReport(path='temp/data/interactive_brokers/test1.xml')
        print(report.topics())

"""
    app = TestApp("127.0.0.1", 4001, 1)

    ibcontract = IBcontract()
    ibcontract.secType = "FUT"
    ibcontract.lastTradeDateOrContractMonth="201706"
    ibcontract.symbol="GBL"
    ibcontract.exchange="DTB"

    ## resolve the contract
    resolved_ibcontract=app.resolve_ib_contract(ibcontract)

    tickerid = app.start_getting_IB_market_data(resolved_ibcontract)

    time.sleep(30)
    """

#ib = IB()
#ib.connect('127.0.0.1', 7496, clientId=1)

#ib.disconnect()

# store historic data in pystore
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

if __name__ == '__main__':
    run()