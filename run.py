from dashboard import datasource


def pipeline():
    pass

pipeline()

ds = datasource.Datasource()
ds.IBKR.connect(read_only=True)
#print(ds.IBKR.client.positions())
print(ds.get_security_historical(
    '360310574', 
    durationStr='3 W', 
    barSizeSetting='1 min', 
    whatToShow='TRADES', 
    useRTH=True, 
    #endDateTime='20190927 23:59:59', 
    updateDB=True))

