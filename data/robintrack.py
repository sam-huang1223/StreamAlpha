"""
For parsing and updating RobinTrack data

Unsure of best practice here - daily downloads of historic data from RobinTrack -> extract and append vs. scraping
"""

"""
for idx, ticker in enumerate(os.listdir('../../data/robintrack/')):
    stock = {
        'ticker' : ticker.split('.')[0],
        'type' : 'STK',
        'ID' : None
    }
    result = instruments.stocks.insert_one(stock)
    print('Created {0} of {1} as {2}'.format(idx, len(os.listdir('data/robintrack/')), result.inserted_id))
"""