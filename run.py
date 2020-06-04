from engine import Engine
from dashboard import charts


def pipeline():
    pass

pipeline()

#engine = Engine(connect=False)
#engine.IBKR.connect(read_only=True)
#print(engine.IBKR.client.positions())
"""
print(engine.IBKR.get_security_historical(
    '360310574', 
    durationStr='3 W', 
    barSizeSetting='1 day', 
    whatToShow='TRADES', 
    useRTH=True, 
    #endDateTime='20190927 23:59:59', 
    updateDB=True))
"""
# see reference here -> https://interactivebrokers.github.io/tws-api/historical_bars.html#hd_request

charts.run_dash(True)