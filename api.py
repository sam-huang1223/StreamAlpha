# package imports
from flask import Flask, request
import configparser
import sqlite3
import json

from engine import Engine

# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

# FUTURE: switch flask -> https://github.com/python-restx/flask-restx ?

# -------------------------------------------

app = Flask(__name__)
app.debug = True

datasource = Datasource()

@app.route('/trades/strategy/<ticker>', methods = ['GET'])
def stock(ticker):
    if request.method == 'GET':
        """
        return all trades related to <ticker> for some given strategy

        :param ticker: some stock ticker
        
        body parameters:
        strategy -> e.g. covered_call
        start_time -> e.g. YYYY-MM-DD HH:MM:SS
        end_time -> e.g. YYYY-MM-DD HH:MM:SS
        allow_naked_calls -> True/False
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
                stock_trades, call_trades = datasource.get_covered_call_trades(conn, ticker, start_time, end_time)
                return {'stock_trades': stock_trades, 'call_trades': call_trades}

if __name__ == '__main__':
    app.run()