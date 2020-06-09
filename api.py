# package imports
from flask import Flask, request
import configparser
import sqlite3
import json

from engine import Engine, Covered_Calls_Strat
import utils.sql_queries as queries

# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

# FUTURE: switch flask -> https://github.com/python-restx/flask-restx ?

# -------------------------------------------

app = Flask(__name__)
app.debug = True

engine = Engine()

@app.route('/portfolio/strategy/<ticker>', methods = ['GET'])
def portfolio_strategy(ticker):
    """
    return all trades related to <ticker> for some given strategy
    :param ticker: some stock ticker
    
    body parameters:
    strategy -> e.g. covered_call
    start_time -> e.g. YYYY-MM-DD HH:MM:SS
    end_time -> e.g. YYYY-MM-DD HH:MM:SS
    """
    data = request.form
    with sqlite3.connect(PROJECT_DB_PATH) as conn:
        try:
            start_time = data['start_time']
        except KeyError:
            start_time = None
        try: 
            end_time = data['end_time']
        except KeyError:
            end_time = None
        if data['strategy'] == 'covered_call':
            covered_call = Covered_Calls_Strat(engine)
            stock_trades, call_trades = covered_call.get_trades(conn, ticker, start_time, end_time)
            cumulative_positions = covered_call.calculate_cumulative_positions(stock_trades, call_trades)
            return cumulative_positions.to_dict(), 200, {'schema': '*insert schema here'}

@app.route('/<ticker>', methods = ['GET'])
def ticker_info(ticker):
    with sqlite3.connect(PROJECT_DB_PATH) as conn:
        result = queries.execute_sql(conn, queries.sql_get_ticker_currency.format(ticker=ticker))[0]

    return {'name': result[0], 'currency': result[1]}, 200

@app.route('/portfolio/stocks', methods = ['GET'])
def portfolio_stocks():
    with sqlite3.connect(PROJECT_DB_PATH) as conn:
        result = queries.execute_sql(conn, queries.sql_get_all_stocks_traded)
    
    return {row[0]: row[1] for row in result}, 200
        

if __name__ == '__main__':
    app.run()