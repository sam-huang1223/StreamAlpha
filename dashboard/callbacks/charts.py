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


def initialize_charts_callbacks(app, label_colors):
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

        min_date = pd.to_datetime(df['execution_time'].min()).date()
        max_date = pd.to_datetime(df['execution_time'].max()).date()

        date_range = max_date - min_date

        # adjust the x-axis min and max to ensure all data is shown
        formatting = {
            'x_min': (min_date - 0.05*date_range).strftime('%Y-%m-%d'),
            'x_max': (max_date + 0.05*date_range).strftime('%Y-%m-%d')
        }

        return json.dumps({'processed_df': df.to_json(orient='split'), 'formatting': json.dumps(formatting)})

    @app.callback(
        dash.dependencies.Output("ticker-strategy-performance-graph", "figure"),
        [
        dash.dependencies.Input("shitty-redis", "children"),
        ],
    )
    def update_ticker_strategy_performance_graph(mem):
        mem = json.loads(mem)
        formatting = json.loads(mem['formatting'])

        df = pd.read_json(mem['processed_df'], orient='split')
        cumulative_positions_time_series = df[df['time_series_flag']]
        
        #ticker_info = requests.get('http://127.0.0.1:5000/{ticker}'.format(ticker=ticker)).json()

        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=cumulative_positions_time_series['execution_time'],
                y=cumulative_positions_time_series['cumulative_value'],
                mode='lines',
                name="Aggregated Performance",
                line={'color': '#7D5125', 'width': 2},
                legendgroup="Performance",
            )
        )

        percent_change_labels = cumulative_positions_time_series[pd.notnull(cumulative_positions_time_series['cumulative_value_percent_change_label'])]

        for row in percent_change_labels.itertuples():
            if row.negative_change_flag == True:
                text_color=label_colors['negative']['text']
                bg_color=label_colors['negative']['bg']
                border_color=label_colors['negative']['border']
            elif row.positive_change_flag == True:
                text_color=label_colors['positive']['text']
                bg_color=label_colors['positive']['bg']
                border_color=label_colors['positive']['border']

            figure.add_annotation(
                x=row.execution_time,
                y=row.cumulative_value,
                text=row.cumulative_value_percent_change_label,
                font={'color': text_color},
                bgcolor=bg_color,
                bordercolor=border_color,
                hovertext=row.option_id,
                #hovertemplate="name: %{y}%{x}<br>number: %{marker.symbol}<extra></extra>"))
            )

        figure.update_annotations(dict(
            xref="x",
            yref="y",
            showarrow=True,
            arrowhead=7,
            ax=0,
            ay=-20,
            font={'size':12},
        ))

        figure.update_layout(
            title='How well did you do?',
            xaxis_title='Date',
            yaxis_title='Total Position',
            showlegend=True,
            legend_orientation="h",
            xaxis_range=[formatting['x_min'], formatting['x_max']],
            #yaxis_range=[y,y],
            #height=600,
            #width=600,
            #uirevision = "The User is always right",  # Ensures zoom on graph is the same on update
        )

        #figure.update_xaxes(tick0=mem['formatting']['x_min'], dtick=1)

        """
        # secondary y-axis looks like a pain to use -> https://github.com/VictorBezak/Plotly_Multi-Axes_Gridlines from https://community.plotly.com/t/line-up-grid-lines-on-multi-axis-plot/4305/11
        # Set x-axis title
        fig.update_xaxes(title_text="xaxis title")

        # Set y-axes titles
        fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
        fig.update_yaxes(title_text="<b>secondary</b> yaxis title", secondary_y=True)
        """

        return figure

    @app.callback(
        dash.dependencies.Output("ticker-options-timing-graph", "figure"),
        [
        dash.dependencies.Input("shitty-redis", "children"),
        ],
    )
    def update_ticker_options_timing_graph(mem):
        mem = json.loads(mem)
        formatting = json.loads(mem['formatting'])

        df = pd.read_json(mem['processed_df'], orient='split')
        cumulative_positions_time_series = df[df['time_series_flag']]

        expired = cumulative_positions_time_series[cumulative_positions_time_series['trade_end_state'] == 'Expired']
        assigned = cumulative_positions_time_series[cumulative_positions_time_series['trade_end_state'] == 'Assigned']
        bought_to_close = cumulative_positions_time_series[cumulative_positions_time_series['trade_end_state'] == 'Bought to Close']
        sold_to_open = cumulative_positions_time_series[cumulative_positions_time_series['trade_end_state'] == 'Sold to Open']
        
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                mode='markers',
                x=expired['execution_time'],
                y=expired['strike'],
                marker_symbol=expired['trade_end_state_symbol'],
                marker_color=expired['trade_end_state_symbol_color'],
                name="Expired",
                legendgroup="Trade End State",
                marker_size=15,
            ),
        )

        figure.add_trace(
            go.Scatter(
                mode='markers',
                x=assigned['execution_time'],
                y=assigned['strike'],
                marker_symbol=assigned['trade_end_state_symbol'],
                marker_color=assigned['trade_end_state_symbol_color'],
                name="Assigned",
                legendgroup="Trade End State",
                marker_size=15,
            ),
        )

        figure.add_trace(
            go.Scatter(
                mode='markers',
                x=bought_to_close['execution_time'],
                y=bought_to_close['strike'],
                marker_symbol=bought_to_close['trade_end_state_symbol'],
                marker_color=bought_to_close['trade_end_state_symbol_color'],
                name="Bought to Close",
                legendgroup="Trade End State",
                marker_size=15,
            ),
        )

        figure.add_trace(
            go.Scatter(
                mode='markers',
                x=sold_to_open['execution_time'],
                y=sold_to_open['strike'],
                marker_symbol=sold_to_open['trade_end_state_symbol'],
                marker_color=sold_to_open['trade_end_state_symbol_color'],
                name="Sold to Open",
                legendgroup="Trade End State",
                marker_size=15,
            ),

"""
        figure.add_trace(
            go.Scatter(
                mode='markers',
                x=sold_to_open['execution_time'],
                y=sold_to_open['strike'],
                marker_symbol=sold_to_open['trade_end_state_symbol'],
                marker_color=sold_to_open['trade_end_state_symbol_color'],
                name="Sold to Open",
                legendgroup="Trade End State",
                marker_size=15,
            ),
"""
        )

        figure.update_layout(
            title='How good was your timing?',
            xaxis_title='Date',
            yaxis_title='Price',
            showlegend=True,
            legend_orientation="h",
            #xaxis_range=[x,x],
            #yaxis_range=[y,y],
            #height=600,
            #width=600,
            #uirevision = "The User is always right",  # Ensures zoom on graph is the same on update
        )

        figure.update_xaxes(range=[formatting['x_min'], formatting['x_max']])

        return figure


# TODO add more ticks in x-axis
# TODO in second chart, also show open short calls as bars in secondary y-axis
    # show
# TODO figure out how to show vertical line on both charts when hovering

"""
    fig = tools.make_subplots(
        rows=2, shared_xaxes=True, shared_yaxes=False, cols=1, print_grid=False
    )
"""