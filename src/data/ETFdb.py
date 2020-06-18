import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import configparser

config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

def get_benchmark_indices(ticker, limit=3, update_db=True):
    r = requests.get(
        'https://etfdb.com/stock/{ticker}'.format(ticker=ticker)
    )         

    soup = BeautifulSoup(r.content, features="html.parser")
    rows = soup.findAll('tr')

    indices = []

    for row in rows[1:limit+1]:
        indices.append({
            'stock_id': row.find('td', {'data-th': 'Ticker'}).text,
            'name': row.find('td', {'data-th': 'ETF'}).text,
            'category': row.find('td', {'data-th': 'ETFdb.com Category'}).text,
            'weight': float(row.find('td', {'data-th': 'Weighting'}).text.strip('%')) / 100
        })

    df = pd.DataFrame.from_dict(indices)

    if update_db:
        with sqlite3.connect(PROJECT_DB_PATH) as conn:
            df.to_sql('Stock_Indices', con=conn, if_exists='append', index=False)

    return df


if __name__ == '__main__':
    print(get_benchmark_indices('CGC'))