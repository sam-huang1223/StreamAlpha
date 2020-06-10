import configparser
import sqlite3

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from shutil import get_terminal_size

import json
import requests
import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', get_terminal_size()[0])

import utils.sql_queries as queries
import dashboard.callbacks.charts as charts


def initialize_charts_callbacks(app):
    @app.callback(
        dash.dependencies.Output("shitty-redis", "children"),  # see https://dash.plotly.com/sharing-data-between-callbacks
        [
        dash.dependencies.Input("ticker-dropdown", "value"),
        dash.dependencies.Input("strategy-dropdown", "value"),
        ],
    )
    def on_ticker_strategy_change(ticker, strategy):
        if not ticker or not strategy:
            return []
        
        if strategy == 'covered call':            
            r = requests.get(
                'http://127.0.0.1:5000/portfolio/strategy/{ticker}'.format(ticker=ticker), 
                data={'strategy': 'covered_call'}
            )         
            #print(r.headers.get('schema'))
        else:
            raise ValueError("apologies! analytics {} is not supported at this time".format(strategy))
        
        df = pd.DataFrame.from_dict(r.json())

        min_date = pd.to_datetime(df['execution_time'].min())
        max_date = pd.to_datetime(df['execution_time'].max())

        date_range = max_date - min_date

        # adjust the x-axis min and max to ensure all data is shown
        formatting = {
            'x_min': (min_date - 0.1*date_range).strftime('%Y-%m-%d %H:%m:%s'),
            'x_max': (max_date + 0.1*date_range).strftime('%Y-%m-%d %H:%m:%s')
        }

        meta = {
            'strategy': strategy,
            'ticker': ticker
        }

        return json.dumps({'processed_df': df.to_json(orient='split'), 'formatting': json.dumps(formatting), 'meta': json.dumps(meta)})

    @app.callback(
        dash.dependencies.Output("all-subplots", "figure"),
        [
        dash.dependencies.Input("shitty-redis", "children"),
        ],
    )
    def update_subplots(mem):
        mem = json.loads(mem)
        formatting = json.loads(mem['formatting'])
        meta = json.loads(mem['meta'])
        processed_df = pd.read_json(mem['processed_df'], orient='split')

        fig = make_subplots(
            2, 1,
            #subplot_titles=("How well did you do?", "How good was your timing?"),
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
        )

        fig = charts.update_ticker_strategy_performance_graph(fig, processed_df, 1, 1)
        fig = charts.update_ticker_options_timing_graph(fig, processed_df, 2, 1)

        fig.update_xaxes(matches='x')

        fig.update_layout(
            height=800, 
            width=1500, 
            title_text="{strategy} on {ticker}".format(strategy=meta['strategy'], ticker=meta['ticker']),
            legend_orientation="v",
            hovermode= 'closest',
            #hoverdistance=-1,
            yaxis2={'nticks': 10, 'tickmode': 'auto'}
        )

        fig.update_xaxes(
            ticks="outside", 
            ticklen=10, 
            range=[formatting['x_min'], formatting['x_max']],
            title_text='Date',

            # for vertical lines show on hover
            showspikes=True,
            spikemode='across',
            spikethickness=1,
            spikedash="solid",
            spikesnap='cursor',
            spikecolor='black'
        )
        
        fig.update_yaxes(
            ticks="outside", 
            ticklen=10,
            fixedrange=True,  # restricts zoom to horizontal
        )


        return fig
        

# TODO in first chart, also show underlying quantity calls as bars in secondary y-axis
# TODO in first chart, also show open short calls as bars in secondary y-axis
    # follow this to fix gridlines issue -> https://github.com/VictorBezak/Plotly_Multi-Axes_Gridlines
    # for y1_max, take max of both underlying price * quantity + cumulative_value

# TODO in second chart, add underlying price + index prices

# TODO "risk taken" as a color range -> % = call premium / stock price, monthly, adjusted for strike price + DTE (ranging from 0% -> 25%)
# TODO remove stock trades with no covered calls (e.g. PD)


# shaded region color (green if strategy was preferable to simply holding stock, clear if similar, red otherwise)
    # use shapes -> https://plotly.com/python/range-slider/
        # copy hoverinfo format from above
