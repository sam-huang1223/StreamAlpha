import configparser
import sqlite3

from .utils import sql_views as views
from .utils import sql_queries as queries

config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH_TEMP = config['DB Path']['PROJECT_DB_PATH_TEMP']
PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

# SQL create table statement for the trade table (based on schema from models.Trade)
CREATE_TABLE_TRADE = """ 
CREATE TABLE IF NOT EXISTS Trade (
                                    trade_id VARCHAR(16) PRIMARY KEY,
                                    trade_type VARCHAR(4) NOT NULL CHECK (trade_type IN ('BUY','SELL')),
                                    security_type VARCHAR(8) NOT NULL CHECK (security_type IN ('STK','OPT','CASH')),
                                    quantity INT NOT NULL,

                                    stock_id VARCHAR(16),  -- not null if security_type is "STK"
                                    option_id VARCHAR(32),  -- not null if security_type is "OPT"

                                    currency CHAR(3) NOT NULL,
                                    fxRateToBase DECIMAL NOT NULL,

                                    execution_time DATETIME NOT NULL,
                                    settle_date DATE NOT NULL,

                                    commission DECIMAL NOT NULL,

                                    price DECIMAL NOT NULL,
                                    total DECIMAL NOT NULL,
                                    base_total DECIMAL NOT NULL,

                                    total_cost_basis DECIMAL,
                                    pnl_realized DECIMAL,

                                    -- below columns are not null if security_type is "CASH" (e.g. currency exchange)
                                    currency_to VARCHAR(4),
                                    currency_from VARCHAR(4),

                                    FOREIGN KEY (stock_id) REFERENCES Stock (stock_id),
                                    FOREIGN KEY (option_id) REFERENCES Option (option_id)
                                    );
"""

# SQL create table statement for the stock table (based on schema from models.Stock)
CREATE_TABLE_STOCK =  """ 
CREATE TABLE IF NOT EXISTS Stock (
                                    stock_id VARCHAR(16) PRIMARY KEY, -- symbol
                                    ib_id VARCHAR(16) NOT NULL,
                                    isin VARCHAR(32) NOT NULL,
                                    exchange VARCHAR(16) NOT NULL,
                                    description TEXT,
                                    currency VARCHAR(4)
                                    );
"""

# SQL create table statement for the option table (based on schema from models.Option)
CREATE_TABLE_OPTION =  """ 
CREATE TABLE IF NOT EXISTS Option (
                                    option_id VARCHAR(32) PRIMARY KEY,  -- description
                                    ib_id VARCHAR(16) NOT NULL,
                                    stock_id VARCHAR(16) NOT NULL, -- ticker
                                    type VARCHAR(1) NOT NULL CHECK (type IN ('P','C')), 
                                    strike DECIMAL NOT NULL,
                                    expiry DATE NOT NULL,
                                    FOREIGN KEY (stock_id) REFERENCES Stock (stock_id) 
                                    );
"""

CREATE_TABLE_DIVIDEND_HISTORY = """
CREATE TABLE IF NOT EXISTS Dividend_History (
                                    dividend_id VARCHAR(32) PRIMARY KEY,  -- Ticker + Ex Date
                                    stock_id VARCHAR(16) NOT NULL, -- ticker
                                    ex_date DATE NOT NULL,
                                    pay_date DATE NOT NULL,
                                    quantity INT NOT NULL,
                                    tax DECIMAL NOT NULL,
                                    amount DECIMAL NOT NULL,
                                    total DECIMAL NOT NULL,
                                    net_total DECIMAL NOT NULL,
                                    FOREIGN KEY (stock_id) REFERENCES Stock (stock_id) 
                                    );
"""

CREATE_TABLE_PRICE_HISTORY_DAY = """
CREATE TABLE IF NOT EXISTS Price_History_Day (
                                    date DATE NOT NULL,
                                    ib_id VARCHAR(16) NOT NULL,
                                    stock_id VARCHAR(16) NOT NULL,
                                    open DECIMAL NOT NULL,
                                    close DECIMAL NOT NULL,
                                    high DECIMAL NOT NULL,
                                    low DECIMAL NOT NULL,
                                    mid DECIMAL NOT NULL,
                                    volume DECIMAL NOT NULL,
                                    FOREIGN KEY (stock_id) REFERENCES Stock (stock_id),
                                    PRIMARY KEY (date, ib_id)
                                    );
"""

CREATE_TABLE_PRICE_HISTORY_HOUR = """
CREATE TABLE IF NOT EXISTS Price_History_Hour (
                                    date DATETIME NOT NULL,
                                    hour INT NOT NULL,
                                    ib_id VARCHAR(16) NOT NULL,
                                    stock_id VARCHAR(16) NOT NULL,
                                    open DECIMAL NOT NULL,
                                    close DECIMAL NOT NULL,
                                    high DECIMAL NOT NULL,
                                    low DECIMAL NOT NULL,
                                    mid DECIMAL NOT NULL,
                                    volume DECIMAL NOT NULL,
                                    FOREIGN KEY (stock_id) REFERENCES Stock (stock_id),
                                    PRIMARY KEY (date, ib_id)
                                    );
"""

CREATE_TABLE_PRICE_HISTORY_MINUTE = """
CREATE TABLE IF NOT EXISTS Price_History_Minute (
                                    date DATETIME NOT NULL,
                                    hour INT NOT NULL,
                                    minute INT NOT NULL,
                                    ib_id VARCHAR(16) NOT NULL,
                                    stock_id VARCHAR(16) NOT NULL,
                                    open DECIMAL NOT NULL,
                                    close DECIMAL NOT NULL,
                                    high DECIMAL NOT NULL,
                                    low DECIMAL NOT NULL,
                                    mid DECIMAL NOT NULL,
                                    volume DECIMAL NOT NULL,
                                    FOREIGN KEY (stock_id) REFERENCES Stock (stock_id),
                                    PRIMARY KEY (date, ib_id)
                                    );
"""

CREATE_TABLE_STOCK_INDICES = """
CREATE TABLE IF NOT EXISTS Stock_Indices (
                                    stock_id VARCHAR(16) NOT NULL,
                                    reference_stock_id VARCHAR(16) NOT NULL,
                                    name TEXT NOT NULL,
                                    category TEXT NOT NULL,
                                    weight DECIMAL NOT NULL,
                                    FOREIGN KEY (reference_stock_id) REFERENCES Stock (stock_id),
                                    PRIMARY KEY (stock_id, reference_stock_id)
                                    );
"""

CREATE_TABLE_PORTFOLIO_HOLDINGS_HISTORY = """
CREATE TABLE IF NOT EXISTS Portfolio_Holdings_History (
                                    date DATE NOT NULL,
                                    stock_id VARCHAR(16) NOT NULL,
                                    quantity INT NOT NULL,
                                    FOREIGN KEY (stock_id) REFERENCES Stock (stock_id),
                                    PRIMARY KEY (date, stock_id)
                                    );
"""


def transfer_table(db_c, table_name):
    column_names = queries.get_table_column_names(db_c, table_name)

    db_c.execute(
        """
        INSERT INTO other.{table} ({columns})
        SELECT {columns} FROM main.{table};
        """.format(
            table = table_name,
            columns = ", ".join(column_names)
        )
    )

DB_TABLE_CREATION_SCRIPTS = [
    CREATE_TABLE_STOCK,
    CREATE_TABLE_OPTION,
    CREATE_TABLE_TRADE,
    CREATE_TABLE_DIVIDEND_HISTORY,
    CREATE_TABLE_PRICE_HISTORY_DAY,
    CREATE_TABLE_PRICE_HISTORY_HOUR,
    CREATE_TABLE_PRICE_HISTORY_MINUTE,
    CREATE_TABLE_STOCK_INDICES,
    CREATE_TABLE_PORTFOLIO_HOLDINGS_HISTORY,
]


def db_creation_script(conn):
    c = conn.cursor()

    print('Initializing the StreamAlpha database ...') # convert to log

    # tables
    for table_creation_script in DB_TABLE_CREATION_SCRIPTS:
        c.execute(table_creation_script)
    # views
    c.execute(views.MOST_RECENT_TRADES)

    print('All tables have been created \n') # convert to log

    conn.commit()

    print("Transfering historic data from temporary database...\n") # convert to log

    temp_db_conn = sqlite3.connect(PROJECT_DB_PATH_TEMP)
    temp_db_c = temp_db_conn.cursor()

    temp_db_c.execute("""
        ATTACH DATABASE '{db_path}' AS other;
        """.format(db_path=PROJECT_DB_PATH)
    )

    TEMP_DB_TABLE_NAMES = queries.get_all_tables(temp_db_c)

    # transfer all tables
    for table_name in TEMP_DB_TABLE_NAMES:
        transfer_table(temp_db_c, table_name)

    temp_db_conn.commit()

    print("Database setup complete! ") # convert to log
    print("-" * 40)


def insert_trade(conn, trade):
    """
    x

    :param conn:
    :param params:
    :return:
    """

    c = conn.cursor()

    if trade.security_type == 'STK':
        sql = """ INSERT INTO Trade(trade_id, trade_type, security_type, quantity, currency, fxRateToBase, execution_time, settle_date, commission, 
              """ + """ price, total, base_total, total_cost_basis, pnl_realized, stock_id)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) """

        params = (trade.order_id, trade.trade_type, trade.security_type, trade.quantity, trade.currency, trade.fxRateToBase, 
                trade.execution_time, trade.settle_date, trade.commission, trade.price, trade.total, trade.base_total, trade.total_cost_basis, trade.pnl_realized, 
                trade.security.ticker)
        c.execute(sql, params)

        if not c.execute("SELECT * FROM Stock WHERE stock_id = '{}'".format(trade.security.ticker)).fetchall():
            insert_stock(c, trade.security.ticker, trade.security.ib_id, trade.security.isin, trade.security.exchange, trade.currency, description=trade.security.description)

        print(
            "Successfully parsed one STOCK {trade_type} of {symbol} on {date}".format(
                    trade_type=trade.trade_type,
                    symbol=trade.security.ticker,
                    date=trade.execution_time,
                )
            ) # convert print statement to log

    elif trade.security_type == 'OPT':
        sql = """ INSERT INTO Trade(trade_id, trade_type, security_type, quantity, currency, fxRateToBase, execution_time, settle_date, commission, 
              """ + """ price, total, base_total, total_cost_basis, pnl_realized, stock_id, option_id)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) """

        params = (trade.order_id, trade.trade_type, trade.security_type, trade.quantity, trade.currency, trade.fxRateToBase, 
                trade.execution_time, trade.settle_date, trade.commission, trade.price, trade.total, trade.base_total, trade.total_cost_basis, trade.pnl_realized, 
                trade.security.underlying, trade.security.name)
        c.execute(sql, params)

        # insert stock_id and ib_id into stock if it does not exist
        if not c.execute("SELECT * FROM Stock WHERE stock_id = '{}'".format(trade.security.underlying)).fetchall():
            insert_stock(c, trade.security.underlying, trade.security.underlying_ib_id, trade.security.underlying_isin, trade.security.underlying_exchange, trade.currency)

        if not c.execute("SELECT * FROM Option WHERE option_id = '{}'".format(trade.security.name)).fetchall():
            insert_option(c, trade)
        
        print(
            "Successfully parsed one OPTION {trade_type} of {symbol} on {date}".format(
                    trade_type=trade.trade_type,
                    symbol=trade.security.name,
                    date=trade.execution_time,
                )
            ) # convert print statement to log

    elif trade.security_type == 'CASH':
        sql = """ INSERT INTO Trade(trade_id, trade_type, security_type, quantity, currency, fxRateToBase, execution_time, settle_date, commission, 
              """ + """ price, total, base_total, total_cost_basis, pnl_realized, currency_to, currency_from)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) """

        params = (trade.order_id, trade.trade_type, trade.security_type, trade.quantity, trade.currency, trade.fxRateToBase, 
                trade.execution_time, trade.settle_date, trade.commission, trade.price, trade.total, trade.base_total, trade.total_cost_basis, trade.pnl_realized, 
                trade.security.currency_to, trade.security.currency_from)
        c.execute(sql, params)
        
        print(
            "Successfully parsed one CASH {trade_type} of {symbol} on {date}".format(
                    trade_type=trade.trade_type,
                    symbol=trade.security.symbol,
                    date=trade.execution_time,
                )
            ) # convert print statement to log


def insert_stock(c, ticker, ib_id, isin, exchange, currency, description=None):
    sql = """ INSERT INTO Stock(stock_id, ib_id, isin, exchange, description, currency)
              VALUES(?,?,?,?,?,?) """

    params = (ticker, ib_id, isin, exchange, currency, description)
    c.execute(sql, params)

def insert_option(c, trade):
    sql = """ INSERT INTO Option(option_id, ib_id, stock_id, type, strike, expiry)
              VALUES(?,?,?,?,?,?) """

    option = trade.security

    params = (option.name, option.ib_id, option.underlying, option.type, option.strike, option.expiry)
    c.execute(sql, params)


def insert_dividend(c, dividend):
    if dividend.code == 'Po':
        sql = """ INSERT INTO Dividend_History(dividend_id, stock_id, ex_date, pay_date, quantity, tax, amount, total, net_total)
                VALUES(?,?,?,?,?,?,?,?,?) """

        params = (dividend.dividend_id, dividend.stock_id, dividend.ex_date, dividend.pay_date, dividend.quantity, dividend.tax, dividend.amount, dividend.total, dividend.net_total)
        c.execute(sql, params)

        print(
            "Successfully parsed {symbol}'s dividend of {net_total} announced on {ex_date} to be paid on {pay_date}".format(
                    symbol=dividend.stock_id,
                    net_total=dividend.net_total,
                    ex_date=dividend.ex_date,
                    pay_date=dividend.pay_date,
                )
        ) # convert print statement to log

def insert_price_history(table_name, conn, prices_df):
    prices_df.to_sql(table_name, con=conn, if_exists='append', index=False)

# sqlite_master is equivalent of MySQL's information_schema