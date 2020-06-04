sql_get_existing_records_dates = """
    SELECT date 
    FROM {table}
    WHERE 
        ib_id = '{ib_id}'
    AND 
        date BETWEEN '{start_date}' AND '{end_date}' 
    ORDER BY date ASC
"""

sql_get_covered_calls_trades_stock = """
    SELECT quantity, execution_time, commission, total, base_total, total_cost_basis, pnl_realized
    FROM Trade
    WHERE
        stock_id = '{ticker}' AND security_type = 'STK'
    {date_range_string}
    ORDER BY 
        execution_time ASC
"""

sql_get_covered_calls_trades_call = """
    SELECT option_id, quantity, execution_time, commission, total, base_total, total_cost_basis, pnl_realized
    FROM Trade
    WHERE
        stock_id = '{ticker}' AND security_type = 'OPT' AND SUBSTR(option_id, -1) = 'C'
    {date_range_string}
    ORDER BY 
        execution_time ASC
"""

sql_get_all_stocks_traded = """
    SELECT DISTINCT stock_id
    FROM Trade
    ORDER BY stock_id ASC
"""

def execute_sql(conn, query_string):
    return conn.cursor().execute(query_string).fetchall()