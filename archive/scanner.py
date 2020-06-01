# can't use ib scanner - results capped at 50 items without market data subscription

"""
scanner_nasdaq = ScannerSubscription(
    instrument='STK', 
    locationCode='STK.NASDAQ', 
    scanCode='HIGH_OPT_IMP_VOLAT')

nasdaq_results = ib.reqScannerData(scanner_nasdaq)

print(f'{len(nasdaq_results)} results, first one:')
print(nasdaq_results[0])
print(nasdaq_results[1])

print()

scanner_nyse = ScannerSubscription(
    instrument='STK', 
    locationCode='STK.NYSE', 
    scanCode='HIGH_OPT_IMP_VOLAT')

nyse_results = ib.reqScannerData(scanner_nyse)

print(f'{len(nyse_results)} results, first one:')
print(nyse_results[0])
print(nyse_results[1])
"""