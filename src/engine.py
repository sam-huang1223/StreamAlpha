import configparser
import ib_insync
import sqlite3
import asyncio

from shutil import get_terminal_size
from multiprocessing import Process
import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', get_terminal_size()[0])
pd.options.mode.chained_assignment = None  # get rid of SettingWithCopyWarning
import pandas_market_calendars as mcal

from numpy import busday_count, datetime64
import datetime as dt
import itertools as it

from .data.IBKR import IBKR
from .data.utils import sql_queries as queries
from .dashboard.settings import SYMBOLS

# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

TRADELOG_PATH = config['XML Paths']['TRADELOG_PATH']
DIVIDEND_HISTORY_PATH = config['XML Paths']['DIVIDEND_HISTORY_PATH']
PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

"""
alternative data sources -> https://www.noeticoptions.com/ (track predictive power?)    
"""
#

class Engine(IBKR):
    def __init__(self, num_clients=32, update_backsups=True):
        """
        This class contains various methods th
        """
        super(Engine, self).__init__(num_clients, update_backsups)

        # ----------------------------- Define Constants ----------------------------- #
        # due to Interactive Broker's API being slow, these constants define "optimal"
        # time intervals for the retrieval of price history (e.g. get minute by minute
        # data 30 days at a time)
        self.MIN_DATA_INTERVAL = dt.timedelta(days=30)
        self.HOUR_DATA_INTERVAL = dt.timedelta(days=365)
        self.DAY_DATA_INTERVAL = dt.timedelta(days=3650) 
        self.holidays = pd.Series(mcal.get_calendar('NYSE').holidays().holidays)
        self.loop = asyncio.get_event_loop()
        # ---------------------------------------------------------------------------- #

    async def _get_price_history_from_api_minute(self, contract_id, start_time, end_time):
        """
        This function chunks requests into multiple API calls, and returns a combined output

        :param start_time: [description]
        :type start_time: [type]
        :param end_time: [description]
        :type end_time: [type]
        """
        # Logic for pulling data from the API in chunks (due to IB API being super slow with large requests)
        # Will always ensure database contains one continuous block of data

        print('[Engine] pulling historic price data with IB API from {start} to {end}'.format(start=start_time, end=end_time))

        df = None  # the final concatenated output
        trading_days = self.MIN_DATA_INTERVAL.days  # number of days of data requested for each API call
        holidays = self.holidays[self.holidays.between(start_time, end_time)].dt.date.tolist()
        end  = end_time  # intermediate variable to keep track of date range window

        # TODO convert this to multi-threaded calls using -> https://creativedata.stream/multi-threading-api-requests-in-python/

        params_list = []  # list of dictionaries of (start, end, trading_days)

        flag = True
        while flag:
            interval_bus_days = busday_count((end - self.MIN_DATA_INTERVAL).date(), end.date() + dt.timedelta(days=1), holidays=holidays)
            start = end - self.MIN_DATA_INTERVAL

            if start < start_time:  # if True, would be the last API call (reached end of date range requested)
                start = start_time
                interval_bus_days = busday_count(start.date(), end.date() + dt.timedelta(days=1), holidays=holidays)
                flag = False

            if end == end_time:
                end_date = end_time
            else:
                end_date = end.date()

            if start == start_time:
                start_date = start_time
            else:
                start_date = start.date()

            params_list.append({
                'start' : start_date,
                'end' : end_date,
                'trading_days' : interval_bus_days,
            })

            end = start

        now = dt.datetime.now()

        # do async calls using up to 32 client IDs (generator?)

        dfs_to_concat = await asyncio.gather(
            *(
                self.get_security_historical_price(
                    contract_id=contract_id, 
                    durationStr="{days} D".format(days=param['trading_days']), 
                    barSizeSetting='1 min', 
                    whatToShow='TRADES', 
                    useRTH=True, 
                    endDateTime=param['end'], 
                    startDateTime=param['start'],
                    updateDB=False,  # CHANGE
                    client=self.clients[idx]
                ) for idx, param in enumerate(params_list)
            )
        )

        print(dt.datetime.now() - now)
        # 0:01:07.358942
        # multi-threaded -> 

        
        output_df = pd.concat(dfs_to_concat, sort=False, ignore_index=True)
        return output_df


    def populate_historical_prices(self, ticker, start_time, end_time, interval):
        """
        Historic data requests from IB API has a timeout issue - therefore, we need to break up requests into smaller chunks
            for minute data -> 1 month at a time works well

        :param ticker: [description]
        :type ticker: [type]
        :param start_time: [description]
        :type start_time: [type]
        :param end_time: a datetime.datetime object specified to the minute (not inclusive)
        :type end_time: [type]
        :return: [description]
        :rtype: [type]
        """        

        if interval == 'minute':
            interval = dt.timedelta(minutes=1)
        # TODO other intervals

        with sqlite3.connect(PROJECT_DB_PATH) as conn:
            contract_id = queries.execute_sql(conn, queries.sql_get_ticker_contract_id.format(ticker=ticker))[0][0]

            min_date_db = queries.execute_sql(conn, queries.sql_get_earliest_price_datetime_minute.format(ticker=ticker))
            max_date_db = queries.execute_sql(conn, queries.sql_get_latest_price_datetime_minute.format(ticker=ticker))

        # if the database has no data on this ticker
        if not min_date_db and not max_date_db:
            print('[Engine] No data in database for {ticker}'.format(ticker=ticker))
            return self.loop.run_until_complete(self._get_price_history_from_api_minute(contract_id, start_time, end_time))
        
        min_date_db = dt.datetime.strptime(min_date_db[0][0], '%Y-%m-%d %H:%M:%S')
        max_date_db = dt.datetime.strptime(max_date_db[0][0], '%Y-%m-%d %H:%M:%S')

        # if the database already contains enough data, pull directly from the database
        missing_beginning_data = \
            (start_time < min_date_db and start_time >= min_date_db.replace(hour=9, minute=30)) or \
            (start_time < min_date_db and start_time <= (min_date_db - dt.timedelta(days=1)).replace(hour=16))
        missing_end_data = end_time > (max_date_db + interval)  # to account for non-inclusive IB API behaviour
        
        dfs_to_concat = []

        if missing_beginning_data: 
            beginning_df = self.loop.run_until_complete(self._get_price_history_from_api_minute(contract_id, start_time, min_date_db))
            beginning_df.rename(columns={'average': 'mid'}, inplace=True)
            dfs_to_concat.append(beginning_df)

            start_time = min_date_db

        
        if missing_end_data:
            end_df = self.loop.run_until_complete(self._get_price_history_from_api_minute(contract_id, max_date_db + interval, end_time))
            end_df.rename(columns={'average': 'mid'}, inplace=True)
            dfs_to_concat.append(end_df)

            end_time = max_date_db
        
        print('[Engine] Pulling from database price history for {ticker} between {start} and {end}'.format(
            ticker=ticker, start=start_time, end=end_time
        ))

        middle_df = pd.DataFrame(
                queries.execute_sql(conn, queries.sql_get_price_minute.format(ticker=ticker, start_date=start_time, end_date=end_time)),
                columns=queries.get_table_column_names(conn.cursor(), 'Price_History_Minute')
            )
        middle_df['date'] = pd.to_datetime(middle_df['date'])
        middle_df.drop(columns=['hour', 'minute', 'ib_id', 'stock_id'], inplace=True)
        dfs_to_concat.append(middle_df)

        output_df = pd.concat(dfs_to_concat, sort=False, ignore_index=True)
        output_df.sort_values('date', axis=0, ascending=True, inplace=True)
        output_df.reset_index(drop=True, inplace=True)

        return output_df

class Covered_Calls_Strat:
    def __init__(self):
        pass

    def get_trades(self, conn, ticker, start_time=None, end_time=None):
        """

        * pnl_realized includes commission - not possible / too complex to factor out given shifting cost basis
        """
        
        date_range_string = ''
        if start_time:
            date_range_string += "AND execution_time >= '{}' ".format(start_time)
        if end_time:
            date_range_string += "AND execution_time <= '{}' ".format(end_time)

        stock_trades_sql = queries.sql_get_covered_calls_trades_stock.format(
            ticker=ticker,
            date_range_string=date_range_string
        )
        call_trades_sql = queries.sql_get_covered_calls_trades_call.format(
            ticker=ticker,
            date_range_string=date_range_string
        )
        
        stock_trades = pd.read_sql_query(stock_trades_sql, conn)
        call_trades = pd.read_sql_query(call_trades_sql, conn)

        # replace pnl_realized as it currently combines PnL from options exercise
        stock_trades['pnl_realized'] = stock_trades['total_cost_basis'] - stock_trades['total']
            
        # cannot realize pnl on purchases only on sales
        stock_trades['pnl_realized'][stock_trades['quantity'] > 0] = None

        # replace pnl_realized as it includes comission paid

        # --- filter out purchased long calls (not part of covered call strategy) ---
        long_call_positions = set()
        
        contracts_covered_placeholder = stock_trades[['execution_time', 'quantity']].rename(columns={'quantity':'underlying_quantity'})
        call_trades = pd.concat([call_trades, contracts_covered_placeholder], sort=False, ignore_index=True)
        call_trades.sort_values('execution_time', axis=0, ascending=True, inplace=True)
        call_trades.reset_index(drop=True, inplace=True)

        call_trades['underlying_quantity'].fillna(0, inplace=True)
        call_trades['contracts_covered'] = (call_trades['underlying_quantity'].cumsum() / 100).astype(int)
        call_trades['open_short_calls'] = None
        call_trades.drop('underlying_quantity', axis=1, inplace=True)

        call_trades.at[0, 'open_short_calls'] = 0

        indices_to_drop = []

        for trade in call_trades.itertuples():
            if trade.Index > 0:
                call_trades.at[trade.Index, 'open_short_calls'] = call_trades.at[trade.Index - 1, 'open_short_calls']

            # if this is a placeholder entry (used to populate contracts_covered)
            if pd.isnull(trade.quantity):
                pass

            # if this trade opens a long call position
            elif trade.quantity > 0 and call_trades.at[trade.Index, 'open_short_calls'] == 0:
                long_call_positions.add(trade.option_id)
            
            # if this trade closes a long call position
            elif trade.quantity < 0 and trade.option_id in long_call_positions:
                long_call_positions.remove(trade.option_id)

            # if this trade is actually part of the covered call strategy
            else:
                if trade.quantity < 0:
                    call_trades.at[trade.Index, 'open_short_calls'] += 1
                elif trade.quantity > 0:
                    call_trades.at[trade.Index, 'open_short_calls'] -= 1
                continue
            
            indices_to_drop.append(trade.Index)

        call_trades.drop(indices_to_drop, inplace=True)
        # ---
        
        # replace pnl_realized as it currently combines PnL from options exercise
        call_trades['pnl_realized'] = call_trades['total_cost_basis']

        # can only realize pnl when calls are bought to close or automatically closed
        call_trades['pnl_realized'][call_trades['quantity'] < 0] = None

        return stock_trades, call_trades

    def calculate_cumulative_positions(self, stock_trades, call_trades):
        df = pd.concat([stock_trades, call_trades], sort=False, ignore_index=True)
        df.sort_values('execution_time', axis=0, ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)

        df = df[['execution_time', 'option_id', 'quantity', 'price', 'fxRateToBase', 'total', 'total_cost_basis', 'commission', 'pnl_realized', 'strike', 'expiry']]

        df['pnl_realized'].fillna(0, inplace=True)
        
        df['value_delta'] = df['total_cost_basis'] - df['total'] + df['commission']  # removes impact of commissions

        df.at[0, 'value_delta'] = df.at[0, 'total_cost_basis']

        # ----------------------- cumulative summation columns ----------------------- #
        df['cumulative_commissions'] = df['commission'].cumsum().abs()
        df['cumulative_value'] = df['value_delta'].cumsum()  # excludes comissions
        df['cumulative_profit'] = df['cumulative_value'] - df['cumulative_commissions'] - df.at[0, "cumulative_value"]
        df['cumulative_cash_investment'] = df['total'].cumsum()  # excludes commissions

        df['cumulative_underlying_quantity'] = df[pd.isnull(df['option_id'])]['quantity']
        df['cumulative_underlying_quantity'].fillna(0, inplace=True)
        df['cumulative_underlying_quantity'] = df['cumulative_underlying_quantity'].cumsum()

        df['yield_on_value'] = (df["cumulative_profit"] / df['cumulative_value'])
        df['yield_on_cash'] = (df["cumulative_profit"] / df['cumulative_cash_investment'])
        # ---------------------------------------------------------------------------- #


        # ----------------------- derived columns for graphing ----------------------- #
        df['time_series_flag'] = True
        df['cumulative_value_percent_change_label'] = pd.Series(None, dtype='str')
        df['negative_change_flag'] = pd.Series(None, dtype='bool')
        df['positive_change_flag'] = pd.Series(None, dtype='bool')

        df['trade_end_state'] = pd.Series(None, dtype='str')
        df['trade_end_state_symbol'] = pd.Series(None, dtype='str')
        df['trade_end_state_symbol_color'] = pd.Series(None, dtype='str')
        # ---------------------------------------------------------------------------- #

        starting_value = df.at[0, "cumulative_value"]

        # compute values for end state of trade (e.g. assigned, expired, bought back, % pnl)
        for order in df.itertuples():
            if not order.Index == 0:
                delta = df.at[order.Index, 'yield_on_value']

                if df.at[order.Index, "cumulative_value"] > df.at[order.Index - 1, "cumulative_value"]:
                    df.at[order.Index, "cumulative_value_percent_change_label"] = "{}%".format(round(delta*100, 2))
                    df.at[order.Index, "positive_change_flag"] = True
                elif df.at[order.Index, "cumulative_value"] < df.at[order.Index - 1, "cumulative_value"]:
                    df.at[order.Index, "cumulative_value_percent_change_label"] = "{}%".format(round(delta*100, 2))
                    df.at[order.Index, "negative_change_flag"] = True

            if pd.isnull(order.option_id):
                # should be nan if trade was referencing a stock
                continue

            if order.quantity < 0:
                df.at[order.Index, 'trade_end_state'] = 'Sold to Open'
                df.at[order.Index, 'trade_end_state_symbol'] = SYMBOLS['shape']['Sold to Open']
                df.at[order.Index, 'trade_end_state_symbol_color'] = SYMBOLS['color']['Sold to Open']
            else:
                if order.total > 0:
                    df.at[order.Index, 'trade_end_state'] = 'Bought to Close'
                    df.at[order.Index, 'trade_end_state_symbol'] = SYMBOLS['shape']['Bought to Close']
                    df.at[order.Index, 'trade_end_state_symbol_color'] = SYMBOLS['color']['Bought to Close']
                elif order.execution_time == df.at[order.Index + 1, 'execution_time']:
                    # if a simultaneous order occured, then it was assigned
                    df.at[order.Index, 'trade_end_state'] = 'Assigned'
                    df.at[order.Index, 'trade_end_state_symbol'] = SYMBOLS['shape']['Assigned']
                    df.at[order.Index, 'trade_end_state_symbol_color'] = SYMBOLS['color']['Assigned']
                    # do not include duplicate order as part of the time series
                    df.at[order.Index + 1, 'time_series_flag'] = False
                elif order.execution_time == df.at[order.Index - 1, 'execution_time']:
                    # if a simultaneous order occured, then it was assigned
                    df.at[order.Index, 'trade_end_state'] = 'Assigned'
                    df.at[order.Index, 'trade_end_state_symbol'] = SYMBOLS['shape']['Assigned']
                    df.at[order.Index, 'trade_end_state_symbol_color'] = SYMBOLS['color']['Assigned']
                    # do not include duplicate order as part of the time series
                    df.at[order.Index - 1, 'time_series_flag'] = False
                else:
                    df.at[order.Index, 'trade_end_state'] = 'Expired'
                    df.at[order.Index, 'trade_end_state_symbol'] = SYMBOLS['shape']['Expired']
                    df.at[order.Index, 'trade_end_state_symbol_color'] = SYMBOLS['color']['Expired']

        return df[['execution_time', 'fxRateToBase', 'commission', 'value_delta', 'cumulative_value', 'yield_on_value', 'cumulative_profit', 'cumulative_commissions', 'cumulative_cash_investment', 'yield_on_cash', 'cumulative_underlying_quantity', 'option_id', 'strike', 'expiry', 'time_series_flag', 'cumulative_value_percent_change_label', 'negative_change_flag', 'positive_change_flag', 'trade_end_state', 'trade_end_state_symbol', 'trade_end_state_symbol_color']]
