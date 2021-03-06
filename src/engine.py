import configparser
import ib_insync
import sqlite3
from shutil import get_terminal_size

import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', get_terminal_size()[0])

import numpy as np

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

pd.options.mode.chained_assignment = None
#

class Engine:
    def __init__(self, connect=True):
        """
        This class contains various methods th
        """
        if connect:
            self.IBKR = IBKR()

    def populate_historical_prices(self, ticker, start_time, end_time):
        #contract_id, durationStr, barSizeSetting, whatToShow, useRTH, endDateTime='', updateDB=True):
        
        self.IBKR.get_security_historical()

        # TODO minute by minute data (always ensure 1 continuous block of min by min data in the DB)


class Covered_Calls_Strat:
    def __init__(self, engine):
        self.engine = engine

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

        df['cumulative_commissions'] = df['commission'].cumsum().abs()
        df['cumulative_value'] = df['value_delta'].cumsum()  # excludes comissions
        df['cumulative_profit'] = df['cumulative_value'] - df['cumulative_commissions'] - df.at[0, "cumulative_value"]
        df['cumulative_cash_investment'] = df['total'].cumsum()  # excludes commissions
        df['cumulative_underlying_quantity'] = df[pd.isnull(df['option_id'])]['quantity'].cumsum()
        df['cumulative_underlying_quantity'].fillna(0, inplace=True)

        df['yield_on_value'] = (df["cumulative_profit"] / df['cumulative_value'])
        df['yield_on_cash'] = (df["cumulative_profit"] / df['cumulative_cash_investment'])

        #print(df)
        #raise SystemError

        # --- derived columns --- #
        df['time_series_flag'] = True
        df['cumulative_value_percent_change_label'] = pd.Series(None, dtype='str')
        df['negative_change_flag'] = pd.Series(None, dtype='bool')
        df['positive_change_flag'] = pd.Series(None, dtype='bool')

        df['trade_end_state'] = pd.Series(None, dtype='str')
        df['trade_end_state_symbol'] = pd.Series(None, dtype='str')
        df['trade_end_state_symbol_color'] = pd.Series(None, dtype='str')
        # --- #

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



        
