import datetime as dt

from src import engine
from src.dashboard.app import DASHboard
from src.data.utils.reset import reset_datastore

#reset_datastore()
e = engine.Engine()

def test(e):
    df = e.populate_historical_prices(
            'AAL',
            start_time=dt.datetime(2020, 3, 22, 10, 0, 0),
            end_time=dt.datetime(2020, 6, 25, 14, 0, 0),
            interval='minute'
        )
    df.plot.line(x='date', y='close')  # visual verification
    import matplotlib.pyplot as plt
    plt.show()

def serve_dashboard():
    dashboard = DASHboard()
    dashboard.serve(debug=True)

#serve_dashboard()

e.connect()
test(e)

"""
Potential solution to historic data retrieval slowless,
where we use an asyncio queue     

1. Functions that use the IB client are producers that add 
to the queue (e.g. IBKR.get_security_historical_price)

2. IB clients (32 with different client IDs) are consumers 
that execute the functions in the queue using their distinct 
connections

^ above solution only works if IB TWS calls actually run 
faster when calls are split across different client IDs
"""