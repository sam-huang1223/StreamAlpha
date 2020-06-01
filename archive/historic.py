"""
Keeping low-usage historic time-series data in parquet form on my laptop (via pystore) to avoid paying cloud hosting fees
    - https://pypi.org/project/PyStore/

Keeping high-usage daily data in MongoDB Atlas

All exposed using an unified Flask API (likely GraphQL via Graphene) - https://github.com/graphql-python/graphene-mongo/blob/master/docs/tutorial.rst
"""

import pystore
import pandas as pd

pystore.set_path('../data/historic/')

instruments = pystore.store('instruments')

stocks = instruments.collection('stocks')
options = instruments.collection('options')

stocks.delete_item("AAPL")

#stocks.write('AAPL', aapl[:-1], metadata={'source': 'Quandl'})
#stocks.append('AAPL', aapl[2:3], npartitions=stocks.item("AAPL").data.npartitions)

"""
use snapshots to protect data - e.g. 

stocks.create_snapshot('snapshot_name')
snap_df = stocks.item('AAPL', snapshot='snapshot_name')
collection.write('AAPL', snap_df.to_pandas(),
                 metadata={'source': 'Quandl'},
                 overwrite=True)
collection.delete_snapshot('snapshot_name')
"""

"""
use metadata

# Query avaialable symbols based on metadata
collection.list_items(source='Quandl')
"""

print(pystore.list_stores())
print(instruments.list_collections())
print(stocks.list_items())

#print(stocks.item("AAPL").to_pandas())


