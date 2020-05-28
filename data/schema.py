# SQL create table statement for the trade table (based on schema from models.Trade)
CREATE_TABLE_TRADE = """ 
CREATE TABLE IF NOT EXISTS Trade (
                                    trade_id VARCHAR(16) PRIMARY KEY,
                                    trade_type VARCHAR(4) NOT NULL CHECK (trade_type IN ('BUY','SELL')),
                                    security_type VARCHAR(8) NOT NULL CHECK (security_type IN ('STK','OPT','CASH')),
                                    quantity INT NOT NULL,

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

                                    stock_id VARCHAR(16),  -- not null if security_type is "STK"
                                    option_id VARCHAR(32),  -- not null if security_type is "OPT"

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
                                    description TEXT
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

def db_creation_script(conn):
    c = conn.cursor()

    c.execute(CREATE_TABLE_STOCK)
    c.execute(CREATE_TABLE_OPTION)
    c.execute(CREATE_TABLE_TRADE)

    conn.commit()

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
            insert_stock(c, trade.security.ticker, trade.security.ib_id, description=trade.security.description)

        print(
            "Successfully parsed one STOCK {trade_type} of {symbol} on {date}".format(
                    trade_type=trade.trade_type,
                    symbol=trade.security.ticker,
                    date=trade.execution_time,
                )
            ) # TODO convert print statement to log

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
            insert_stock(c, trade.security.underlying, trade.security.underlying_ib_id)

        if not c.execute("SELECT * FROM Option WHERE option_id = '{}'".format(trade.security.name)).fetchall():
            insert_option(c, trade)
        
        print(
            "Successfully parsed one OPTION {trade_type} of {symbol} on {date}".format(
                    trade_type=trade.trade_type,
                    symbol=trade.security.name,
                    date=trade.execution_time,
                )
            ) # TODO convert print statement to log

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
            ) # TODO convert print statement to log


def insert_stock(c, ticker, ib_id, description=None):
    sql = """ INSERT INTO Stock(stock_id, ib_id, description)
              VALUES(?,?,?) """

    params = (ticker, ib_id, description)
    c.execute(sql, params)

def insert_option(c, trade):
    sql = """ INSERT INTO Option(option_id, ib_id, stock_id, type, strike, expiry)
              VALUES(?,?,?,?,?,?) """

    option = trade.security

    params = (option.name, option.ib_id, option.underlying, option.type, option.strike, option.expiry)
    c.execute(sql, params)


# sqlite_master is equivalent of MySQL's information_schema