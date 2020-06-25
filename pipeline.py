import configparser
import sqlite3
import datetime as dt

from src import engine
from src.data.utils import sql_queries as queries
from src.data.ETFdb import get_benchmark_indices

config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

### use airflow to orchestrate pipeline

# https://airflow.apache.org/docs/stable/start.html

def run_pipeline(start_date, end_date):
    # TODO pull all data for all stocks (one day at a time, for all positions held that day)
    pass


def run_daily_before_trading_starts():
    e = engine.Engine()  # to update trade history and dividend history
    e.connect()

    today = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - dt.timedelta(days=1)

    current_stocks = [
        # TODO pull all data for positions held yesterday
        holding[0] for holding in
        e.get_portfolio_holdings_daterange(yesterday, today)
    ]

    top_benchmark_etfs = []
    for ticker in current_stocks:
        top_benchmark_etfs.append(
            get_benchmark_indices(ticker=ticker, limit=1, only_db=True)
        )

    # get yesterday's prices for all stock holdings in the portfolio
    for ticker, benchmark in zip(current_stocks, top_benchmark_etfs):
        e.populate_historical_prices(
            ticker=ticker, 
            start_time=yesterday,
            end_time=today,
            interval='minute'
        )

        if len(benchmark.index) > 0:
            e.populate_historical_prices(
                ticker=benchmark['name'].iloc[0], 
                start_time=yesterday,
                end_time=today,
                interval='minute'
            )

    # write script such that when run, would "front-load" computations that need to occur daily

if __name__ == '__main__':
    run_daily_before_trading_starts()

