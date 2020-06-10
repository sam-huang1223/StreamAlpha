import ib_insync

import sqlite3
import configparser
import xml.etree.ElementTree as ET

from datetime import datetime
from types import SimpleNamespace

from data import models
from data import schema

import utils.sql_queries as queries

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
        self.connected = False
        self._setup()

    def _setup(self):
        print('Initializing IBKR Connection...\n')

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
            schema.db_creation_script(self.conn)
            print('Loading tradelog...')
            self.query_flexreport('420983', savepath=TRADELOG_PATH)
            self.parse_tradelog(loadpath=TRADELOG_PATH)

            print('Loading dividend history...')
            self.query_flexreport('421808', savepath=DIVIDEND_HISTORY_PATH)
            self.parse_dividend_history(loadpath=DIVIDEND_HISTORY_PATH)

        # update tradelog if last update was more than 1 day ago
        try:
            doc = ET.parse(TRADELOG_PATH)

            tradelog_datetime_str = list(doc.iter('FlexStatement'))[0].attrib['whenGenerated']
            tradelog_datetime = datetime.strptime(tradelog_datetime_str, '%Y%m%d;%H%M%S')
        except OSError:
            # create tradelog if it doesn't exist
            print('Generating Tradelog...\n')
            self.query_flexreport('420983', savepath=TRADELOG_PATH)
            tradelog_datetime = datetime.now()

        # update dividend history if last update was more than 1 day ago
        try:
            doc = ET.parse(DIVIDEND_HISTORY_PATH)

            dividend_history_datetime_str = list(doc.iter('FlexStatement'))[0].attrib['whenGenerated']
            dividend_history_datetime = datetime.strptime(dividend_history_datetime_str, '%Y%m%d;%H%M%S')
        except OSError:
            # create dividend history if it doesn't exist
            print('Generating Dividend History...\n')
            self.query_flexreport('421808', savepath=DIVIDEND_HISTORY_PATH)
            dividend_history_datetime = datetime.now()

        # if there are new entries, parse the updated tradelog into db
        print('Checking Tradelog...')
        if (datetime.now().day - tradelog_datetime.day) > 0:
            self.query_flexreport('420983', savepath=TRADELOG_PATH)
            print('Updating Tradelog...')
            self._update_tradelog_db(last_updated=tradelog_datetime)
        print('Tradelog is up-to-date\n')
        
        # if there are new entries, parse the updated dividend history in db
        print('Checking Dividend History..')
        if (datetime.now().day - dividend_history_datetime.day) > 0:
            self.query_flexreport('421808', savepath=DIVIDEND_HISTORY_PATH)
            print('Updating Dividend History...')
            self._update_dividend_history_db(last_updated=dividend_history_datetime)
        print('Dividend History is up-to-date\n')
        
        print('IBKR Connection Successfully Established\n')

    def __del__(self):
        self.conn.close()
        if self.connected:
            self.disconnect()

    def connect(self, read_only=True):
        self.client.connect('127.0.0.1', 7496, clientId=1, readonly=read_only)
        self.connected = True
        print('Connected to IB TWS')

    def disconnect(self):
        self.client.disconnect()
        self.connected = False
        print('Disconnected from IB TWS')

    def query_flexreport(self, queryID, savepath):
        """
        Programmatically queries a flex report (must be manually defined in the IBKR interface)
            see -> https://www.interactivebrokers.com/en/software/am/am/reports/activityflexqueries.htm

        :param queryID: same as ID from IBKR flex query interface
        :param savepath: output path for xml file
        :return: N/A (only writes to log)
        """
        try:
            trades = ib_insync.FlexReport(self.IBKR_FLEXREPORT_TOKEN, queryID)
            trades.save(savepath)
            ib_insync.flexreport._logger.info('Flex Query has been saved at {}'.format(savepath))
        except Exception as e:
            print(e.message, e.args)
            raise e

    def parse_tradelog(self, loadpath):
        print('Parsing tradelog...')
        report = ib_insync.FlexReport(path=loadpath)
        
        # convert all mentions of Trade to Order
        for order in report.extract('Order'):  # don't use "Trade" as an order may be fulfilled with multiple trades
            schema.insert_trade(self.conn, models.Trade(order))

        self.conn.commit()

    def parse_dividend_history(self, loadpath):
        print('Parsing dividend history...')
        dividend_history = ib_insync.FlexReport(path=loadpath)
        
        for dividend in dividend_history.extract('ChangeInDividendAccrual'):
            div = models.Dividend(dividend)
            # only consider accrued dividend postings (i.e. not reversals on paid out dividends) <- assumes dividends don't get cancelled
            if div.code == 'Po':
                schema.insert_dividend(self.conn, div)
        
        self.conn.commit()

    def _update_tradelog_db(self, last_updated):
        last_tradelog = ET.parse(TRADELOG_PATH)

        # filter for new orders to insert into the database
        for record in last_tradelog.iter('Order'):
            # orders occured on the same day do not get updated in the tradelog until the day after
            if datetime.strptime(record.attrib['dateTime'], '%Y%m%d;%H%M%S') >= last_updated:
                order = SimpleNamespace(**record.attrib)
                schema.insert_trade(self.conn, models.Trade(order))

        self.conn.commit()

    def _update_dividend_history_db(self, last_updated):
        # update dividend history if last update was more than 1 day ago
        last_dividend_history = ET.parse(DIVIDEND_HISTORY_PATH)

        # filter for new dividends to insert into the database

        for record in last_dividend_history.iter('ChangeInDividendAccrual'):
            if datetime.strptime(record.attrib['exDate'], '%Y%m%d') >= last_updated:
                dividend = SimpleNamespace(**record.attrib)
                schema.insert_dividend(self.conn, models.Dividend(dividend))
                

        self.conn.commit()

    def get_security_historical(self, contract_id, durationStr, barSizeSetting, whatToShow, useRTH, endDateTime='', updateDB=True):
        """

        Note: cannot be used for expired options - alternative here (https://www.ivolatility.com/)
        """
        assert self.connected, "Must connect to IBKR's Trader Workstation application before using this function"

        # create contract object uing the unique contract ID
        contract = ib_insync.Contract(conId = contract_id)
        self.client.qualifyContracts(contract)

        # use the IBKR API to get historical data
        bars = self.client.reqHistoricalData(
            contract, endDateTime=endDateTime, durationStr=durationStr,
            barSizeSetting=barSizeSetting, whatToShow=whatToShow, useRTH=useRTH)

        # convert to pandas dataframe
        df = ib_insync.util.df(bars)

        if updateDB:
            df['stock_id'] = contract.symbol
            df['ib_id'] = contract_id
            df = df.astype({"date": str})
            df = df.drop(columns=['average', 'barCount'])

            if 'day' in barSizeSetting:
                price_history_table = 'Price_History_Day'
            elif 'hour' in barSizeSetting:
                price_history_table = 'Price_History_Hour'
                df['hour'] = df['date'].str.split(" ").str[1].str.split(':').str[0]
            elif 'min' in barSizeSetting:
                price_history_table = 'Price_History_Minute'
                df['hour'] = df['date'].str.split(" ").str[1].str.split(':').str[0]
                df['minute'] = df['date'].str.split(" ").str[1].str.split(':').str[1]
            else:
                raise ValueError("price data with bar size of {} cannot be inserted into the database".format(barSizeSetting))
        
            start_date = df['date'].min()
            end_date = df['date'].max()
            sql_execute = queries.sql_get_existing_records_dates.format(table=price_history_table, ib_id = contract_id, start_date=start_date, end_date=end_date)
            
            df['mid'] = (df['high'] + df['low']) / 2
            
            dates_already_in_db = [date[0] for date in queries.execute_sql(self.conn, sql_execute)]
            df_new_records = df[~df['date'].isin(dates_already_in_db)]
            schema.insert_price_history(price_history_table, self.conn, df_new_records)

        return df

    """

    def option_IV(self):
        assert self.connected, "Must connect to IBKR's Trader Workstation application before using this function"

        option = ib_insync.Option('EOE', '20171215', 490, 'P', 'FTA', multiplier=100)
        calc = self.client.calculateImpliedVolatility(
            option, optionPrice=6.1, underPrice=525
        )

        print(calc)

        calc = self.client.calculateOptionPrice(
            option, volatility=0.14, underPrice=525
        )

        print(calc)
    """


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
