import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
import plotly.graph_objects as go

import pandas as pd

from ..settings import LABEL_COLORS, FILL_COLORS
from .helper import unfuck_gridlines, hex_to_rgb


def update_ticker_strategy_performance_graph(fig, processed_df, plot_row, plot_col):
    cumulative_positions_time_series = processed_df[processed_df['time_series_flag']]
    
    fig.add_trace(
        go.Scatter(
            x=cumulative_positions_time_series['execution_time'],
            y=cumulative_positions_time_series['cumulative_value'],
            mode='lines',
            name="Aggregated Performance",
            line={'color': '#7D5125', 'width': 2},
            legendgroup="Performance",
        ),
        plot_row,
        plot_col
    )

    fig.add_trace(
        go.Scatter( 
            x=cumulative_positions_time_series['execution_time'], 
            y=cumulative_positions_time_series['cumulative_underlying_quantity'],
            name='Underlying Quantity Held',
            line_shape='hv',
            fill='tozeroy',
            mode='none',
            fillcolor=f"rgba{(*hex_to_rgb(FILL_COLORS['underlying_quantity']), 0.75)}",
        ),
        plot_row,
        plot_col,
        secondary_y=True,
    )

    percent_change_labels = cumulative_positions_time_series[pd.notnull(cumulative_positions_time_series['cumulative_value_percent_change_label'])]
    for row in percent_change_labels.itertuples():
        if row.negative_change_flag == True:
            text_color=LABEL_COLORS['negative']['text']
            bg_color=LABEL_COLORS['negative']['bg']
            border_color=LABEL_COLORS['negative']['border']
        elif row.positive_change_flag == True:
            text_color=LABEL_COLORS['positive']['text']
            bg_color=LABEL_COLORS['positive']['bg']
            border_color=LABEL_COLORS['positive']['border']
        fig.add_annotation(
            x=row.execution_time,
            y=row.cumulative_value,
            text=row.cumulative_value_percent_change_label,
            font={'color': text_color},
            bgcolor=bg_color,
            arrowcolor=bg_color,
            bordercolor=bg_color,
            hovertext=row.option_id,
            #hovertemplate="name: %{y}%{x}<br>number: %{marker.symbol}<extra></extra>"))
        )
    fig.update_annotations(dict(
        xref="x",
        yref="y",
        showarrow=True,
        ax=-10,
        ay=-20,
        font={'size':11},
        arrowhead=7,
        arrowsize=1,
        arrowwidth=2.5,
        borderwidth=2,
        opacity=0.8
    ))

    fig.update_yaxes(
        title_text='Total Position',
        row=plot_row,
        col=plot_col
    )

    fig.update_xaxes(
        ### really cool plotly magic for adjusting daterange on graph (see https://plotly.com/python/range-slider/)
        rangeslider_visible=False,
        rangeselector=dict(
        buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ]
            )
        ),
        ###
        row=plot_row,
        col=plot_col
    )

        

    """
    # secondary y-axis looks like a pain to use -> https://github.com/VictorBezak/Plotly_Multi-Axes_Gridlines from https://community.plotly.com/t/line-up-grid-lines-on-multi-axis-plot/4305/11
    # Set y-axes titles
    fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
    fig.update_yaxes(title_text="<b>secondary</b> yaxis title", secondary_y=True)
    """
    return fig


def update_ticker_options_timing_graph(fig, processed_df, plot_row, plot_col):
    cumulative_positions_time_series = processed_df[processed_df['time_series_flag']]

    expired = cumulative_positions_time_series[cumulative_positions_time_series['trade_end_state'] == 'Expired']
    assigned = cumulative_positions_time_series[cumulative_positions_time_series['trade_end_state'] == 'Assigned']
    bought_to_close = cumulative_positions_time_series[cumulative_positions_time_series['trade_end_state'] == 'Bought to Close']
    sold_to_open = cumulative_positions_time_series[cumulative_positions_time_series['trade_end_state'] == 'Sold to Open']
    
    fig.add_trace(
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
        plot_row,
        plot_col
    )
    fig.add_trace(
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
        plot_row,
        plot_col
    )
    fig.add_trace(
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
        plot_row,
        plot_col
    )
    fig.add_trace(
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
        plot_row,
        plot_col
    )

    fig.update_yaxes(
        title_text='Price',
        row=plot_row,
        col=plot_col
    )
    
    return fig