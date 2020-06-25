import ib_insync

import sqlite3
import configparser
import xml.etree.ElementTree as ET
from shutil import move, copyfile
from os.path import exists

import datetime
from types import SimpleNamespace
from pandas import to_datetime

from . import models
from . import schema

from .utils import sql_queries as queries

# ----------------------------------- admin ---------------------------------- #
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']
TRADELOG_PATH = config['XML Paths']['TRADELOG_PATH']
TRADELOG_BACKUP_PATH = config['Backup Paths']['TRADELOG_BACKUP_PATH']
DIVIDEND_HISTORY_BACKUP_PATH = config['Backup Paths']['DIVIDED_HISTORY_BACKUP_PATH']
DIVIDEND_HISTORY_PATH = config['XML Paths']['DIVIDEND_HISTORY_PATH']
TRADE_HISTORY_FLEX_REPORT_ID = config['IB Flex Report IDs']['TRADE_HISTORY']
DIVIDEND_HISTORY_FLEX_REPORT_ID = config['IB Flex Report IDs']['DIVIDEND_HISTORY']
# ---------------------------------------------------------------------------- #

class IBKR:
    def __init__(self, update_backups=False):
        self.connected = False
        self.update_backups = update_backups
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

        # get datetime of last trade
        try:
            last_trade_datetime = datetime.datetime.strptime(
                queries.execute_sql(self.conn, queries.sql_get_last_trade_datetime)[0][0], 
                '%Y-%m-%d %H:%M:%S'
            )
        except IndexError:
            last_trade_datetime = None

        try:
            doc = ET.parse(TRADELOG_PATH)
            tradelog_datetime_str = list(doc.iter('FlexStatement'))[0].attrib['whenGenerated']
            tradelog_datetime = datetime.datetime.strptime(tradelog_datetime_str, '%Y%m%d;%H%M%S')
        except OSError:
            tradelog_datetime = None

        # get date of last dividend
        try:
            last_dividend_date = datetime.datetime.strptime(
                queries.execute_sql(self.conn, queries.sql_get_last_dividend_datetime)[0][0],
                '%Y-%m-%d'
            )
        except IndexError:
            last_dividend_date = None

        try:
            doc = ET.parse(DIVIDEND_HISTORY_PATH)
            dividend_history_datetime_str = list(doc.iter('FlexStatement'))[0].attrib['whenGenerated']
            dividend_history_datetime = datetime.datetime.strptime(dividend_history_datetime_str, '%Y%m%d;%H%M%S')
        except OSError:
            dividend_history_datetime = None

        # hypothesis -> new trades from today can be retrieved after midnight 
        # if there are new entries, parse the updated tradelog into db
        print('Checking Tradelog...')
        empty_trade_table = not last_trade_datetime  # if Trade table is empty
        out_of_date_trade_table = not tradelog_datetime or (datetime.datetime.now().day - last_trade_datetime.day) > 1 and (datetime.datetime.now().day - tradelog_datetime.day) > 0
        
        if empty_trade_table or out_of_date_trade_table:
            print('Downloading Tradelog...')
            try:
                if self.update_backups and exists(TRADELOG_PATH):
                    move(TRADELOG_PATH, TRADELOG_BACKUP_PATH)
                self.query_flexreport(TRADE_HISTORY_FLEX_REPORT_ID, savepath=TRADELOG_PATH)
            except ib_insync.flexreport.FlexError as download_error:
                # if cannot download for whatever reason (e.g. API limit exceeded), use backup
                copyfile(TRADELOG_BACKUP_PATH, TRADELOG_PATH)
                print(download_error)
            print('Updating Tradelog...')
            self._update_tradelog_db(last_updated=last_trade_datetime)
        print('Tradelog is up-to-date\n')
        
        # if there are new entries, parse the updated dividend history in db
        print('Checking Dividend History...')
        empty_dividend_history_table = not last_dividend_date  # if Dividend_History table is empty
        out_of_date_dividend_history_table = not dividend_history_datetime or (datetime.datetime.now().day - last_dividend_date.day) > 1 and (datetime.datetime.now().day - dividend_history_datetime.day) > 0
        
        if empty_dividend_history_table or out_of_date_dividend_history_table:
            print('Downloading Dividend History...')
            try:
                if self.update_backups and exists(DIVIDEND_HISTORY_PATH):
                    move(DIVIDEND_HISTORY_PATH, DIVIDEND_HISTORY_BACKUP_PATH)
                self.query_flexreport(DIVIDEND_HISTORY_FLEX_REPORT_ID, savepath=DIVIDEND_HISTORY_PATH)
            except ib_insync.flexreport.FlexError as download_error:
                # if cannot download for whatever reason (e.g. API limit exceeded), use backup
                copyfile(DIVIDEND_HISTORY_BACKUP_PATH, DIVIDEND_HISTORY_PATH)
                print(download_error)
            print('Updating Dividend History...')
            self._update_dividend_history_db(last_updated=last_dividend_date)
        print('Dividend History is up-to-date\n')

        self._compute_portfolio_holdings_history()
        
        print('IBKR Connection Successfully Established')
        print("-" * 40)

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

    def _compute_portfolio_holdings_history(self):
        pass
        # TODO

    def query_flexreport(self, queryID, savepath):
        """
        Programmatically queries a flex report (must be manually defined in the IBKR interface)
            see -> https://www.interactivebrokers.com/en/software/am/am/reports/activityflexqueries.htm

        :param queryID: same as ID from IBKR flex query interface
        :param savepath: output path for xml file
        :return: N/A (only writes to log)
        """
        report = ib_insync.FlexReport(self.IBKR_FLEXREPORT_TOKEN, queryID)
        report.save(savepath)
        print("Download Complete!\n")
        # convert below to project logging
        ib_insync.flexreport._logger.info('Flex Query has been saved at {}'.format(savepath))

    def _update_tradelog_db(self, last_updated):
        last_tradelog = ET.parse(TRADELOG_PATH)

        # filter for new orders to insert into the database
        for record in last_tradelog.iter('Order'):
            # orders occured on the same day do not get updated in the tradelog until the day after
            if not last_updated or datetime.datetime.strptime(record.attrib['dateTime'], '%Y%m%d;%H%M%S') > last_updated:
                order = SimpleNamespace(**record.attrib)
                schema.insert_trade(self.conn, models.Trade(order))

        self.conn.commit()

    def _update_dividend_history_db(self, last_updated):
        # update dividend history if last update was more than 1 day ago
        last_dividend_history = ET.parse(DIVIDEND_HISTORY_PATH)

        # filter for new dividends to insert into the database

        for record in last_dividend_history.iter('ChangeInDividendAccrual'):
            if not last_updated or datetime.datetime.strptime(record.attrib['exDate'], '%Y%m%d') > last_updated:
                dividend = SimpleNamespace(**record.attrib)
                schema.insert_dividend(self.conn, models.Dividend(dividend))
                

        self.conn.commit()

    def get_security_historical_price(self, contract_id, durationStr, barSizeSetting, whatToShow, useRTH, endDateTime='', startDateTime='', updateDB=True):
        """

        Note: cannot be used for expired options - alternative here (https://www.ivolatility.com/)
        """
        assert self.connected, "Must connect to IBKR's Trader Workstation application before using this function"

        print('\t[IBKR] pulling historic price data for {days} trading days to {end}'.format(days=durationStr, end=endDateTime))

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
            df = df.drop(columns=['barCount'])

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
            
            df.rename(columns={'average': 'mid'}, inplace=True)
            df['date'] = to_datetime(df['date'])

            # checks for adherence to time boundaries if time is specified
            if type(startDateTime) is datetime.datetime or type(endDateTime) is datetime.datetime:
                df = df[df.date.between(startDateTime, endDateTime)]

            print(df)
            schema.insert_price_history(price_history_table, self.conn, df)

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
