import configparser
import sqlite3

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import json
import requests

import utils.sql_queries as queries
from engine import Engine

app = dash.Dash(__name__)

# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

conn = sqlite3.connect(PROJECT_DB_PATH)

# --- execute necessary prelimary steps --- #
dropdown_options_raw = queries.execute_sql(conn, queries.sql_get_all_stocks_traded)

engine = Engine(connect=False)
#

app.layout = html.Div(
    [
        html.Label(
            [
                "Select a stock from the portfolio",
                dcc.Dropdown(
                    id="ticker-dropdown",
                    options=[{'label': ticker[0], 'value': ticker[0]} for ticker in dropdown_options_raw if ticker[0]],
                    placeholder="enter ticker here",
                )
            ]
        ),

        html.Label(
            [
                "Select a trading strategy",
                dcc.Dropdown(
                    id="strategy-dropdown",
                    options=[{'label': 'covered call', 'value': 'covered call'}],
                    placeholder="enter strategy name here",
                )
            ]
        ),

        dcc.Graph(
            id='strategy-performance-graph',
            figure={}
        ),

        html.Div(id='test', children=[])
    ]
)

@app.callback(
    dash.dependencies.Output("strategy-performance-graph", "options"),
    #dash.dependencies.Output("test", "children"),
    [
    dash.dependencies.Input("ticker-dropdown", "value"),
    dash.dependencies.Input("strategy-dropdown", "value")
    ],
)
def update_chart(ticker, strategy):
    if not ticker or not strategy:
        return None
    
    with sqlite3.connect(PROJECT_DB_PATH) as conn:
        if strategy == 'covered call':
            trades = engine.get_covered_call_trades(conn, ticker)
            
            r = requests.get('http://127.0.0.1:5000/trades/strategy/AC', data={'strategy': 'covered_call'})
            trades = r.json()            
            #print(r.headers.get('schema'))
        else:
            raise ValueError("apologies! analytics {} is not supported at this time".format(strategy))
    
    figure = trades
        
    return figure


def run_dash(debug=False):
    app.run_server(debug=debug)
    conn.close()