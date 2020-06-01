"""
* get historic prices for options and stock

if can get high + low -> https://plotly.com/python/candlestick-charts/
otherwise -> https://plotly.com/python/time-series/


1. make (solid) line of realized value
2. make (dotted) line of unrealized value
3. make overlaying bar graph that shows cash inflow/outflow (e.g. buy/sell, dividends, etc.)
    https://plotly.com/python/graphing-multiple-chart-types/
data required #TODO
1. price history for underlying
2. price histories for calls sold during holding period
3. dividend history (+ TODO add to schema)

EXTENSION:
4. plot a point for the "optimal" strike at which a call could have been sold, for every time a call was sold (could be ITM or OOTM) (in blue)
    easily calculated as min(strike) where strike > closing price on day of call expiry
4. plot a dotted line for potential maximum value realized had "optimal" strikes been chosen (in blue)
data required
1. entire options chain
2. price history on chosen option with "optimal" strikes
    * best to get price history on entire options chain if it is feasible


bar chart below (with same date range)
1. gain/loss due to delta
2. gain/loss due to theta
3. gain/loss due to vega


FUTURE ROADMAP
    1. [calculated] in hindset, most optimal sequence of options to sell from date_range_start -> date_range_end
        (represented by lines (y-axis - strike, x-axis - buy to expiry date)) 
        + "optimal" line of maximal possible realized value (assuming full length hold)
        + comparison to relevant indices (e.g. industry, optimal SPY covered call strategy)
        + comparison to "best possible" realized value from a covered call strategy for any one stock in the relevant industry
        + for optimality calculation, allow for options buyback + immediate selling of new option
        data required:
        a fuckton
    2. x

"""