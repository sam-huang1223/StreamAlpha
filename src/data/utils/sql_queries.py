sql_get_covered_calls_trades_stock = """
    SELECT quantity, price, execution_time, commission, total, base_total, total_cost_basis, pnl_realized, fxRateToBase
    FROM Trade
    WHERE
        stock_id = '{ticker}' AND security_type = 'STK'
    {date_range_string}
    ORDER BY 
        execution_time ASC
"""

sql_get_covered_calls_trades_call = """
    SELECT Trade.option_id, quantity, price, execution_time, commission, total, base_total, total_cost_basis, pnl_realized, fxRateToBase, strike, expiry
    FROM Trade
    JOIN Option
    ON Trade.option_id = Option.option_id
    WHERE
        Trade.stock_id = '{ticker}' AND security_type = 'OPT' AND SUBSTR(Trade.option_id, -1) = 'C'
    {date_range_string}
    ORDER BY 
        execution_time ASC
"""

sql_get_ticker_currency = """
    SELECT currency, description
    FROM Stock
    WHERE stock_id = '{ticker}'
"""

sql_get_ticker_contract_id = """
    SELECT ib_id
    FROM Stock
    WHERE stock_id = '{ticker}'
"""

sql_get_all_stocks_traded = """
    SELECT DISTINCT stock_id, ib_id
    FROM Stock
    ORDER BY stock_id ASC
"""

sql_get_last_trade_datetime = """
    SELECT execution_time 
    FROM Trade
    ORDER BY execution_time DESC
    LIMIT 1
"""

sql_get_last_dividend_datetime = """
    SELECT ex_date 
    FROM Dividend_History
    ORDER BY ex_date DESC
    LIMIT 1
"""

sql_get_earliest_price_datetime_minute = """
    SELECT date
    FROM Price_History_Minute
    WHERE stock_id = '{ticker}'
    ORDER BY date ASC
    LIMIT 1
"""

sql_get_latest_price_datetime_minute = """
    SELECT date
    FROM Price_History_Minute
    WHERE stock_id = '{ticker}'
    ORDER BY date DESC
    LIMIT 1
"""

sql_get_price_minute = """
    SELECT *
    FROM Price_History_Minute
    WHERE stock_id = '{ticker}'
    AND date >= '{start_date}' 
    AND date <= '{end_date}'
    ORDER BY date DESC
"""

def get_table_column_names(c, table_name):
    return [
        column[1] for column in c.execute(
            """
            PRAGMA table_info({table_name})
            """.format(table_name=table_name)
        ).fetchall()
    ]

def get_all_tables(c):
    return [table[0] for table in
        c.execute("""
            SELECT 
                name
            FROM 
                sqlite_master 
            WHERE 
                type ='table' AND name NOT LIKE 'sqlite_%';
        """).fetchall()
    ]

def execute_sql(conn, query_string):
    return conn.cursor().execute(query_string).fetchall()

# for testing purposes
if __name__ == '__main__':
    import sqlite3
    import configparser
    config = configparser.ConfigParser()
    with open('config.ini') as f:
        config.read_file(f)

    PROJECT_DB_PATH_TEMP = config['DB Path']['PROJECT_DB_PATH_TEMP']
    PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

    temp_db_conn = sqlite3.connect(PROJECT_DB_PATH_TEMP)
    temp_db_c = temp_db_conn.cursor()

    print(get_all_tables(temp_db_c))