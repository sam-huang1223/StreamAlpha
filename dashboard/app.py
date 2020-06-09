"""
maybe https://plotly.com/python/getting-started-with-chart-studio/ for hosting?
multi page support + URLs -> https://dash.plotly.com/urls

FUTURE -> embed into flask app (https://medium.com/@olegkomarov_77860/how-to-embed-a-dash-app-into-an-existing-flask-app-ea05d7a2210b)
"""

import configparser
import sqlite3
import requests

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly import tools

import utils.sql_queries as queries

# --- execute necessary prelimary steps --- #config = configparser.ConfigParser()
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

COLORS = {
    'background': '#202B33',
    'text': '#BFCCD6',
    'toggles': '#293742',
}

SIZES = {
    'background': '#',
    'text': '#',
    'toggles': 50,
}

LABEL_COLORS = {
    'positive': {
        'bg': '#62D96B',
        'text': '#1D7324',
        'border': '#29A634',
    },
    'negative': {
        'bg': '#FF7373',
        'text': '#A82A2A',
        'border': '#DB3737',
    }
}

SYMBOLS = {
    'shape': {
        'Expired': 'triangle-up',
        'Assigned': 'square',
        'Sold to Open': 'triangle-right',
        'Bought to Close': 'triangle-left',
    },
    'color': {
        'Assigned': '#D9822B',
        'Expired': '#29A634',
        'Sold to Open': '#137CBD',
        'Bought to Close': '#137CBD',
    }
}


class DASHboard:
    def __init__(self):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
            #    "https://codepen.io/chriddyp/pen/bWLwgP.css"
            ]
        )

        self.conn = sqlite3.connect(PROJECT_DB_PATH)

    def serve(self, debug):
        self.precompute()
        self.set_DASHboard_layout()

        # hacky way of separating callbacks into separate files
        from dashboard.callbacks import charts
        charts.initialize_charts_callbacks(self.app, LABEL_COLORS)

        self.app.run_server(debug=debug)

    def precompute(self):
        self.portfolio_stocks_list = [stock for stock in requests.get('http://127.0.0.1:5000/portfolio/stocks').json().keys()]

    def set_DASHboard_layout(self):
        self.app.layout = html.Div(#style={'backgroundColor': self.colors['background']}, 
            children=[
            html.Label(
                [
                    "Select a stock from the portfolio",
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[{'label': ticker, 'value': ticker} for ticker in self.portfolio_stocks_list],
                        placeholder="enter ticker here",
                        value='AC',
                    )
                ],
                #style={
                #    'color': self.colors['text']
                #}
            ),
            html.Label(
                [
                    "Select a trading strategy",
                    dcc.Dropdown(
                        id="strategy-dropdown",
                        options=[{'label': 'covered call', 'value': 'covered call'}],
                        placeholder="enter strategy name here",
                        value='covered call',
                    )
                ],
                #style={
                #    'color': self.colors['text']
                #}
            ),
            daq.ToggleSwitch(
                id='forgone-upside-toggle',
                value=False,
                size=SIZES['toggles'],
                color=COLORS['toggles'],
                label='Show forgone upside from assignment',
                labelPosition='left',
                #style={
                #    'color': self.colors['text']
                #}
            ),
            dcc.Graph(
                id='ticker-strategy-performance-graph',
                figure={},
                config={"displayModeBar": True, "scrollZoom": True},
            ),
            dcc.Graph(
                id='ticker-options-timing-graph',
                figure={},
                config={"displayModeBar": True, "scrollZoom": True},
            ),
            html.Div(id='shitty-redis', children=[], style={'display': 'none'})
            ]
        )

