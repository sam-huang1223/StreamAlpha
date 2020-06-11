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
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly import tools

from ..data.utils import sql_queries as queries

# --- execute necessary prelimary steps --- #config = configparser.ConfigParser()
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']


class DASHboard:
    def __init__(self):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
            #    "https://codepen.io/chriddyp/pen/bWLwgP.css",
            #    "https://unpkg.com/tachyons@4.10.0/css/tachyons.min.css",
                dbc.themes.BOOTSTRAP
            ],
            suppress_callback_exceptions = True
        )

        self.conn = sqlite3.connect(PROJECT_DB_PATH)

    def serve(self, debug):
        self.precompute()
        self.set_DASHboard_layout()

        # hacky way of separating callbacks into separate files
        from .callbacks import drivers
        drivers.initialize_charts_callbacks(self.app)
        drivers.initialize_layout_callbacks(self.app, self.portfolio_stocks_list)

        self.app.run_server(debug=debug, dev_tools_silence_routes_logging=True)

    def precompute(self):
        self.portfolio_stocks_list = [stock for stock in requests.get('http://127.0.0.1:5000/portfolio/stocks').json().keys()]

    def set_DASHboard_layout(self):
        self.app.layout = html.Div(
            children=[
                html.H1(
                    id='dashboard-title',
                    children='Options Trading Assistant'
                ),
                html.Div(id='tabs-div', children=[
                    dcc.Tabs(
                        id='dashboard-tabs', value='tab-1', children=[
                            dcc.Tab(label='Tab 1', value='tab-1'),
                            dcc.Tab(label='Tab 2', value='tab-2'),
                        ]
                    ),
                    dbc.Spinner(
                        id='tab-loading-spinner', 
                        children=[
                            html.Div(id="tab-content"),
                            html.Div(id='shitty-redis', style={'display': 'none'})
                        ], 
                        spinner_style={"width": "3rem", "height": "3rem"},  #https://dash-bootstrap-components.opensource.faculty.ai/docs/components/spinner/
                    ),
                ]
                )
            ]
        )

# debugging advice -> https://community.plotly.com/t/solved-dash-layout-not-working-as-expected-general-debugging-tips/4724