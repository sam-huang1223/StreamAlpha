# package imports
from flask import Flask, request
import configparser
import sqlite3
import json

# admin
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']

# FUTURE: switch flask -> https://github.com/python-restx/flask-restx ?

# -------------------------------------------

app = Flask(__name__)
app.debug = True

@app.route('/trades/strategy/<ticker>', methods = ['GET'])
def stock(ticker):
    if request.method == 'GET':
        """
        return all trades related to <ticker> for some given strategy

        example params:
        strategy -> covered_call
        """

        data = request.form

        with sqlite3.connect(PROJECT_DB_PATH) as tradelog:
            c = tradelog.cursor()

            if data['strategy'] == 'covered_call':
                return (
                    json.dumps(
                    {idx: trade for idx, trade in enumerate(
                            c.execute("""  
                                SELECT 
                                        T.stock_id, S.description, T.option_id, T.trade_type, 
                                        T.execution_time, O.strike, O.expiry,
                                        T.quantity, T.price, T.total, T.commission,
                                        T.total_cost_basis, T.pnl_realized, T.fxRateToBase,
                                        T.base_total, T.security_type, T.currency
                                FROM (
                                    SELECT *
                                    FROM Trade 
                                    WHERE Trade.security_type IN ('STK', 'OPT')
                                        AND Trade.stock_id = '{ticker}'                   
                                    ) AS T
                                LEFT JOIN Stock S
                                ON T.stock_id = S.stock_id
                                LEFT JOIN Option O
                                ON T.option_id = O.option_id
                                WHERE O.type = 'C' OR O.type IS NULL
                                ORDER BY T.execution_time
                            """.format(ticker=ticker)
                            ).fetchall()
                        )
                    }
                ), 
                200, 
                {'schema': ['stock_id', 'description', 'option_id', 'trade_type', 
                            'execution_time', 'strike', 'expiry',
                            'quantity', 'price', 'total', 'commission',
                            'total_cost_basis', 'pnl_realized', 'fxRateToBase',
                            'base_total', 'security_type', 'currency'
                        ]
                    }
                )
            else:
                return "Error - Strategy not available"

if __name__ == '__main__':
    app.run()