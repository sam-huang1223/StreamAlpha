from src.dashboard.app import DASHboard

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

dashboard = DASHboard()
dashboard.serve(debug=True)

# TODO - write "destroy script to reset db + xml files"