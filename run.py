from dashboard import datasource


def pipeline():
    pass

pipeline()

ds = datasource.Datasource(connect=False)
#ds.IBKR.connect(read_only=True)
#print(ds.IBKR.client.positions())
"""
print(ds.IBKR.get_security_historical(
    '360310574', 
    durationStr='3 W', 
    barSizeSetting='1 day', 
    whatToShow='TRADES', 
    useRTH=True, 
    #endDateTime='20190927 23:59:59', 
    updateDB=True))
"""

a, b = ds.get_covered_call_trades('AC', '', '')

print(a)

print(b)
