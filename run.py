from dashboard.app import DASHboard

import sqlite3
import configparser

import engine


# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

conn = sqlite3.connect(PROJECT_DB_PATH)


def pipeline():
    pass

pipeline()

#e = engine.Engine(connect=True)

"""
e = engine.Engine(connect=False)
cc = engine.Covered_Calls_Strat(e)
s, c = cc.get_trades(conn, 'AC')
print(cc.calculate_cumulative_positions(s, c))
"""

#engine.IBKR.connect(read_only=True)
#print(engine.IBKR.client.positions())
"""
print(engine.IBKR.get_security_historical(
    '360310574', 
    durationStr='3 W', 
    barSizeSetting='1 day', 
    whatToShow='TRADES', 
    useRTH=True, 
    #endDateTime='20190927 23:59:59', 
    updateDB=True))
"""
# see reference here -> https://interactivebrokers.github.io/tws-api/historical_bars.html#hd_request

dashboard = DASHboard()
dashboard.serve(debug=True)

# TODO - write "destroy script to reset db + xml files"