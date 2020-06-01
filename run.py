from dashboard import datasource


def pipeline():
    pass

pipeline()

ds = datasource.Datasource()
ds.IBKR.connect(read_only=True)
#print(ds.IBKR.client.positions())
#print(ds.get_security_historical('360310574', durationStr='2 W', barSizeSetting='1 hour', whatToShow='TRADES', useRTH=True, updateDB=False))

