import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import configparser
from datetime import datetime
from time import sleep

from .utils import sql_queries as queries

config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

def _check_db(ticker, limit):
    with sqlite3.connect(PROJECT_DB_PATH) as conn:
        indices_in_db = pd.DataFrame(
            queries.execute_sql(
                conn, 
                queries.sql_get_benchmark_tickers.format(
                    ticker=ticker, limit=limit
                )
            ),
            columns=queries.get_table_column_names(conn.cursor(), 'Stock_Indices')
        )
    return indices_in_db

def _check_ETFdb(ticker, limit, update_db):
    print('Checking ETFDB.com for {ticker}'.format(ticker=ticker))

    if '.' in ticker:
        short_ticker = ticker.split('.')[0]
    else:
        short_ticker = ticker

    r = requests.get(
        'https://etfdb.com/stock/{ticker}'.format(ticker=short_ticker)
    )         

    soup = BeautifulSoup(r.content, features="html.parser")
    rows = soup.findAll('tr')

    indices = []

    for row in rows[1:limit+1]:
        try:
            indices.append({
                'stock_id': row.find('td', {'data-th': 'Ticker'}).text,
                'reference_stock_id': ticker,
                'name': row.find('td', {'data-th': 'ETF'}).text,
                'category': row.find('td', {'data-th': 'ETFdb.com Category'}).text,
                'weight': float(row.find('td', {'data-th': 'Weighting'}).text.strip('%')) / 100,
            })
        except AttributeError:  # means etfdb.com could not find the stock
            return pd.DataFrame()

    df = pd.DataFrame.from_dict(indices)

    if update_db:
        with sqlite3.connect(PROJECT_DB_PATH) as conn:
            df.to_sql('Stock_Indices', con=conn, if_exists='append', index=False)

    sleep(3)  # to ensure we don't overload API and get temporarily IP banned

    return df

def get_benchmark_indices(ticker, limit=3, only_db=False, update_db=True):
    """


    Limitations:
    -> works better for med-large cap US stocks (can only 
    see ETFs related to some stock if that stock is within 
    the ETF's top 15 holdings (no premium account))
    -> may not direct to the right stock (e.g. AC direct to
    Associate Capital group instead of Air Canada)

    :param ticker: [description]
    :type ticker: [type]
    :param limit: [description], defaults to 3
    :type limit: int, optional
    :param update_db: [description], defaults to True
    :type update_db: bool, optional
    :return: [description]
    :rtype: [type]
    """
    indices_in_db = _check_db(ticker, limit)
    num_indices_in_db = len(indices_in_db.index)

    if num_indices_in_db >= limit or only_db:
        print('Pulling data from database for {ticker}'.format(ticker=ticker))
        return indices_in_db[:limit]
    else:
        limit = limit - num_indices_in_db

    etfdb_indices = _check_ETFdb(ticker, limit, update_db)

    if len(etfdb_indices.index) == 0:
        return indices_in_db

    if num_indices_in_db > 0:
        return pd.concat([indices_in_db, etfdb_indices], ignore_index=True)
    else:
        return etfdb_indices


if __name__ == '__main__':
    print(get_benchmark_indices('CGC'))