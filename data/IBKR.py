import ib_insync

import sqlite3
import configparser


from .schema import db_creation_script, insert_trade, insert_dividend
from .models import Trade, Dividend

"""
import requests

r = requests.post("http://localhost:5000/stock/AAL", data={'ID': "1234567"})
print(r.status_code, r.reason)
print(r.text)
"""

# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']
TRADELOG_PATH = config['XML Paths']['TRADELOG_PATH']
DIVIDEND_HISTORY_PATH = config['XML Paths']['DIVIDEND_HISTORY_PATH']


class IBKR:
    def __init__(self):
        self._setup()
        self.connected = False

    def _setup(self):
        # admin
        config = configparser.ConfigParser()

        # config.ini contains sensitive credentials
        with open('credentials.ini') as f:
            config.read_file(f)
        self.IBKR_FLEXREPORT_TOKEN = str(config['IB API']['IBKR_FLEXREPORT_TOKEN'])

        # initialize instance of client
        self.client = ib_insync.IB()

        if PROJECT_DB_PATH:
            self.conn = sqlite3.connect(PROJECT_DB_PATH)
        else:
            self.conn = sqlite3.connect(':memory:')

        # run creation script if DB is empty
        if not self.conn.cursor().execute("SELECT name FROM sqlite_master WHERE type ='table' AND name NOT LIKE 'sqlite_%';").fetchall():
            db_creation_script(self.conn)
            print('Loading tradelog...')
            self.query_flexreport('420983', savepath=TRADELOG_PATH)
            self.parse_tradelog(loadpath=TRADELOG_PATH)

            print('Loading dividend history...')
            self.query_flexreport('421808', savepath=DIVIDEND_HISTORY_PATH)
            self.parse_dividend_history(loadpath=DIVIDEND_HISTORY_PATH)

    def __del__(self):
        self.conn.close()
        self.disconnect()

    def connect(self, read_only):
        self.client.connect('127.0.0.1', 7496, clientId=1, readonly=read_only)
        self.connected = True
        print('Connected to IB TWS')

    def disconnect(self):
        self.client.disconnect()
        self.connected = False
        print('Disconnected from IB TWS')

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

    def parse_tradelog(self, loadpath):
        print('Parsing tradelog...')
        report = ib_insync.FlexReport(path=loadpath)
        
        # TODO convert all mentions of Trade to Order
        for order in report.extract('Order'):  # don't use "Trade" as an order may be fulfilled with multiple trades
            insert_trade(self.conn, Trade(order))

        self.conn.commit()

    def parse_dividend_history(self, loadpath):
        print('Parsing dividend history...')
        dividend_history = ib_insync.FlexReport(path=loadpath)
        
        for dividend in dividend_history.extract('ChangeInDividendAccrual'):
            div = Dividend(dividend)
            # only consider accrued dividend postings (i.e. not reversals on paid out dividends) <- assumes dividends don't get cancelled
            if div.code == 'Po':
                insert_dividend(self.conn, div)
        
        self.conn.commit()


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


"""
stock = Stock('SUPV', '', 'USD')
out = ib.reqContractDetails(stock)

print(out)

chains = ib.reqSecDefOptParams(, '', 'STK', 233587209)

chains = util.df(chains)

# update chain parameters weekly

print(chains)
"""
