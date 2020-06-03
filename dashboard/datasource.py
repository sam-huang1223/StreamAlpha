"""
data required #TODO
1. price history for underlying
2. price histories for calls sold during holding period
3. dividend history (+ TODO add to schema)
"""

from dash.dependencies import Input, Output, State
from datetime import datetime
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import configparser
import sqlite3
import ib_insync

from data import IBKR
from data import models
from data import schema


# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

TRADELOG_PATH = config['XML Paths']['TRADELOG_PATH']
DIVIDEND_HISTORY_PATH = config['XML Paths']['DIVIDEND_HISTORY_PATH']

class Datasource:
    def __init__(self, force_update_tradelog=False, force_update_dividend_history=False):
        # initialize connection to IBKR
        self.IBKR = IBKR()
        self._setup(force_update_tradelog, force_update_dividend_history)

    def _setup(self, force_update_tradelog, force_update_dividend_history):
        print('Initializing Datasource...')
        # update tradelog if last update was more than 1 day ago
        try:
            print('Checking Tradelog...')
            doc = ET.parse(TRADELOG_PATH)

            tradelog_datetime_str = list(doc.iter('FlexStatement'))[0].attrib['whenGenerated']
            tradelog_datetime = datetime.strptime(tradelog_datetime_str, '%Y%m%d;%H%M%S')
        except OSError:
            # create tradelog if it doesn't exist
            print('Generating Tradelog...')
            self.IBKR.query_flexreport('420983', savepath=TRADELOG_PATH)
            tradelog_datetime = datetime.now()

        # update dividend history if last update was more than 1 day ago
        try:
            print('Checking Dividend History...')
            doc = ET.parse(DIVIDEND_HISTORY_PATH)

            dividend_history_datetime_str = list(doc.iter('FlexStatement'))[0].attrib['whenGenerated']
            dividend_history_datetime = datetime.strptime(dividend_history_datetime_str, '%Y%m%d;%H%M%S')
        except OSError:
            # create dividend history if it doesn't exist
            print('Generating Dividend History...')
            self.IBKR.query_flexreport('421808', savepath=DIVIDEND_HISTORY_PATH)
            dividend_history_datetime = datetime.now()

        if (datetime.now() - tradelog_datetime).days > 0 or force_update_tradelog:
            # parse the updated tradelog
            self.IBKR.query_flexreport('420983', savepath=TRADELOG_PATH)
            # insert the differentials into the project DB
            print('Updating Tradelog...')
            self._update_tradelog_db(last_updated=tradelog_datetime)
        print('Tradelog is up-to-date')

        if (datetime.now() - dividend_history_datetime).days > 0 or force_update_dividend_history:
            # parse the updated dividend history
            self.IBKR.query_flexreport('421808', savepath=DIVIDEND_HISTORY_PATH)
            # insert the differentials into the project DB
            print('Updating Dividend History...')
            self._update_dividend_history_db(last_updated=dividend_history_datetime)
        print('Dividend History is up-to-date')
        
        print('Datasource established')

    def _update_tradelog_db(self, last_updated):
        last_tradelog = ET.parse(TRADELOG_PATH)

        # filter for new orders to insert into the database
        for record in last_tradelog.iter('Order'):
            # orders occured on the same day do not get updated in the tradelog until the day after
            if datetime.strptime(record.attrib['dateTime'], '%Y%m%d;%H%M%S').date() >= last_updated.date():
                order = SimpleNamespace(**record.attrib)
                schema.insert_trade(self.IBKR.conn, models.Trade(order))

        self.IBKR.conn.commit()

    def _update_dividend_history_db(self, last_updated):
        # update dividend history if last update was more than 1 day ago
        last_dividend_history = ET.parse(DIVIDEND_HISTORY_PATH)

        # filter for new dividends to insert into the database

        for record in last_dividend_history.iter('ChangeInDividendAccrual'):
            if datetime.strptime(record.attrib['exDate'], '%Y%m%d').date() >= last_updated.date():
                dividend = SimpleNamespace(**record.attrib)
                schema.insert_dividend(self.IBKR.conn, models.Dividend(dividend))
                

        self.IBKR.conn.commit()

    def get_security_historical(self, contract_id, durationStr, barSizeSetting, whatToShow, useRTH, endDateTime='', updateDB=True):
        """

        Note: cannot be used for expired options - alternative here (https://www.ivolatility.com/)
        """
        assert self.IBKR.connected, "Must connect to IBKR's Trader Workstation application before using this function"

        # create contract object uing the unique contract ID
        contract = ib_insync.Contract(conId = contract_id)
        self.IBKR.client.qualifyContracts(contract)

        # use the IBKR API to get historical data
        bars = self.IBKR.client.reqHistoricalData(
            contract, endDateTime=endDateTime, durationStr=durationStr,
            barSizeSetting=barSizeSetting, whatToShow=whatToShow, useRTH=useRTH)

        # convert to pandas dataframe
        df = ib_insync.util.df(bars)

        if updateDB:
            df['stock_id'] = contract.symbol
            df['ib_id'] = contract_id
            df = df.astype({"date": str})
            df = df.drop(columns=['average', 'barCount'])

            sql_get_existing_records = """
                SELECT date 
                FROM {table}
                WHERE 
                ib_id = '{ib_id}'
                    AND 
                date BETWEEN '{start_date}' AND '{end_date}' 
                ORDER BY date ASC
            """

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
            sql_execute = sql_get_existing_records.format(table=price_history_table, ib_id = contract_id, start_date=start_date, end_date=end_date)
            
            dates_already_in_db = [date[0] for date in self.IBKR.conn.cursor().execute(sql_execute).fetchall()]
            df = df[~df['date'].isin(dates_already_in_db)]
            schema.insert_price_history(price_history_table, self.IBKR.conn, df)

        return df

    """

    def option_IV(self):
        assert self.IBKR.connected, "Must connect to IBKR's Trader Workstation application before using this function"

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
