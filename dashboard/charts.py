import configparser
import sqlite3

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
import plotly.graph_objects as go

import json
import requests
import pandas as pd

import utils.sql_queries as queries

app = dash.Dash(
    __name__,
    external_stylesheets=[
#        "https://codepen.io/chriddyp/pen/bWLwgP.css"
    ]
)

colors = {
    'background': '#',
    'text': '#',
    'toggles': '#293742',
}

sizes = {
    'background': '#',
    'text': '#',
    'toggles': 50,
}


# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

@app.callback(
    dash.dependencies.Output("strategy-performance-graph", "figure"),
    [
    dash.dependencies.Input("ticker-dropdown", "value"),
    dash.dependencies.Input("strategy-dropdown", "value"),
    ],
)
def update_chart(ticker, strategy):
    if not ticker or not strategy:
        return {}
    
    with sqlite3.connect(PROJECT_DB_PATH) as conn:
        if strategy == 'covered call':            
            r = requests.get(
                'http://127.0.0.1:5000/portfolio/strategy/{ticker}'.format(ticker=ticker), 
                data={'strategy': 'covered_call'}
            )         
            #print(r.headers.get('schema'))
        else:
            raise ValueError("apologies! analytics {} is not supported at this time".format(strategy))

    cumulative_positions = pd.DataFrame.from_dict(r.json())
    cumulative_positions_time_series = cumulative_positions[cumulative_positions['time_series_flag']]
    
    ticker_info = requests.get('http://127.0.0.1:5000/{ticker}'.format(ticker=ticker)).json()

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=cumulative_positions_time_series['execution_time'],
            y=cumulative_positions_time_series['cumulative_value'],
            mode='lines+markers',
            name="Aggregated Performance",
            line={'color': '#7D5125', 'width': 2}
        )
    )

    figure.update_layout(
        title='Strategy Analytics: {strategy} on {ticker}'.format(strategy=strategy, ticker=ticker),
        xaxis_title='Date',
        yaxis_title=ticker_info['currency'] + ' Position'
    )
        
    return figure


def run_dash(debug=False):
    conn = sqlite3.connect(PROJECT_DB_PATH)

    # --- execute necessary prelimary steps --- #
    dropdown_options_raw = queries.execute_sql(conn, queries.sql_get_all_stocks_traded)
    #

    # --- #
    app.layout = html.Div(
        [
            html.Label(
                [
                    "Select a stock from the portfolio",
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[{'label': ticker[0], 'value': ticker[0]} for ticker in dropdown_options_raw if ticker[0]],
                        placeholder="enter ticker here",
                        value='AC',
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
                        value='covered call',
                    )
                ]
            ),

            daq.ToggleSwitch(
                id='forgone-upside-toggle',
                value=False,
                size=sizes['toggles'],
                color=colors['toggles'],
                label='Show forgone upside from assignment',
                labelPosition='left'
            ),

            dcc.Graph(
                id='strategy-performance-graph',
                figure={}
            ),

            html.Div(id='test', children=[])
        ]
    )


    # --- #

    app.run_server(debug=debug)
    conn.close()