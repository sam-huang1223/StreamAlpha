import configparser
import sqlite3

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash_table import DataTable
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from shutil import get_terminal_size
from time import sleep
from datetime import datetime

import json
import requests
from numpy import nan
import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', get_terminal_size()[0])
pd.options.mode.chained_assignment = None  # get rid of SettingWithCopyWarning

from ...data.utils import sql_queries as queries
from ...data.etfdb import get_benchmark_indices
from . import charts
from .. import settings

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
        
        strategy = strategy.lower().replace(' ', '_')

        if strategy == 'covered_call':            
            r = requests.get(
                'http://127.0.0.1:5000/portfolio/strategy/{ticker}'.format(ticker=ticker), 
                data={'strategy': strategy}
            )         
            #print(r.headers.get('schema'))
        else:
            raise ValueError("apologies! the {} strategy is not supported at this time".format(strategy))
        
        df = pd.DataFrame.from_dict(r.json())

        min_date = pd.to_datetime(df['execution_time'].min())
        max_date = pd.to_datetime(df['execution_time'].max())

        # for graphing purposes
        if df["cumulative_underlying_quantity"].iloc[-1] > 0:
            now = datetime.today().replace(microsecond=0)
            max_date = now
        
            last_row = df.iloc[[-1]]
            last_row['execution_time'] = str(datetime.today().replace(microsecond=0))
            last_row['commission'] = 0
            last_row['expiry'] = nan
            last_row['strike'] = nan
            last_row['option_id'] = nan
            last_row['negative_change_flag'] = nan
            last_row['positive_change_flag'] = nan
            last_row['cumulative_value_percent_change_label'] = nan
            last_row['trade_end_state'] = nan
            last_row['trade_end_state_symbol'] = nan
            last_row['trade_end_state_symbol_color'] = nan
            last_row['value_delta'] = 0
            df = df.append(last_row, ignore_index=True)

        date_range = max_date - min_date

        # adjust the x-axis min and max to ensure all data is shown
        formatting = {
            'x_min': (min_date - 0.2*date_range).strftime('%Y-%m-%d %H:%m:%s'),
            'x_max': (max_date + 0.2*date_range).strftime('%Y-%m-%d %H:%m:%s')
        }

        meta = {
            'strategy': strategy,
            'ticker': ticker
        }

        historical_prices = requests.get(
            'http://127.0.0.1:5000/historical/price/{ticker}'.format(ticker=ticker), 
            data={'start_day': min_date.day, 'end_day': max_date.day}
        )
        historical_prices_df = pd.DataFrame.from_dict(historical_prices.json())


        return json.dumps(
            {
                'processed_df': df.to_json(orient='split'), 
                'historical_prices_df': historical_prices_df.to_json(orient='split'),
                'formatting': json.dumps(formatting), 
                'meta': json.dumps(meta)
            }
        )

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
            yaxis2={'nticks': 10, 'tickmode': 'auto'},
            xaxis_rangeslider_visible=False,
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
        

def initialize_layout_callbacks(app, portfolio_stocks):
    @app.callback(
        Output('tab-content', 'children'),
        [Input('dashboard-tabs', 'value')]
    )
    def render_tabs(tab_value):
        if tab_value == 'tab-1':
            return render_tab_one()
        elif tab_value == 'tab-2':
            return render_tab_two()

    def render_tab_one():
        return [
            html.Label(
                [
                    "Select a stock from the portfolio",
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[{'label': ticker, 'value': ticker} for ticker in portfolio_stocks],
                        placeholder="enter ticker here",
                        value='AC',
                    )
                ],
            ),
            html.Label(
                [
                    "Select a trading strategy",
                    dcc.Dropdown(
                        id="strategy-dropdown",
                        options=[{'label': 'Covered Call', 'value': 'Covered Call'}],
                        placeholder="enter strategy name here",
                        value='Covered Call',
                    )
                ],
            ),
            html.Div(id='toggles-div', children=[
                daq.ToggleSwitch(
                    id='forgone-upside-toggle',
                    value=False,
                    size=settings.SIZES['toggles'],
                    color=settings.COLORS['toggles'],
                    label='Show forgone upside from assignment',
                    labelPosition='left',
                    #style={
                    #    'color': self.colors['text']
                    #}
                ),
                # TODO convert this to a DataTable 
                """
                dcc.Dropdown(
                    id="benchmark-index-dropdown",
                    options=None,
                    placeholder="choose an index to benchmark against",
                    value=None
                ),
                """
            ]),
            dcc.Graph(
                id='all-subplots',
                figure={},
                config={"displayModeBar": True, "scrollZoom": True},
            ),
        ]

    def render_tab_two():
        return html.Div([

        ])
 

# use https://plotly.com/python/candlestick-charts/ for underlying price


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
