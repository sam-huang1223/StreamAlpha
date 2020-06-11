MOST_RECENT_TRADES = """
CREATE VIEW most_recent_trades 
AS 

SELECT
    *
FROM
	Trade
ORDER BY
    execution_time DESC
LIMIT 10
"""