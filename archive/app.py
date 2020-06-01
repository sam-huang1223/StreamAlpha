# package imports
from flask import Flask, request
from pymongo import MongoClient
import configparser


# admin
config = configparser.ConfigParser()
# config.ini contains sensitive credentials
with open('config.ini') as f:
    config.read_file(f)
MONGODB_ATLAS_PASSWORD = config['MongoDB Atlas']['MONGODB_ATLAS_PASSWORD']

app = Flask(__name__)
app.debug = True

client = MongoClient('mongodb+srv://streamalpha:{password}@streamalpha-o9mip.mongodb.net/test?retryWrites=true&w=majority'.format(password=MONGODB_ATLAS_PASSWORD))
instruments = client.instruments

@app.route('/stock/<ticker>', methods = ['GET', 'POST', 'DELETE'])
def stock(ticker):
    if request.method == 'GET':
        """return the information for stock"""
        raise NotImplementedError

    elif request.method == 'POST':
        """upsert for stock <ticker>"""
        data = request.form

        query = {'ticker': ticker}
        replacement = {'ID':data['ID'], 'ticker':ticker}

        instruments.stocks.replace_one(
            filter=query,
            replacement=replacement,
            upsert=True
        )
        return "Stock {ticker} now has properities {properties}".format(ticker=ticker, properties=replacement)

    elif request.method == 'DELETE':
        """delete stock with ticker <ticker>"""
        raise NotImplementedError


@app.route('/option/<ID>', methods = ['GET', 'POST', 'DELETE'])
def option(ID):
    if request.method == 'GET':
        """return the information for option"""
        raise NotImplementedError

    elif request.method == 'POST':
        """upsert for option <ID>"""
        data = request.form

        instruments.option.replace_one(
            filter={'ID': ID},
            replacement={},  # TODO
            upsert=True
        )

    elif request.method == 'DELETE':
        """delete option with ID <ID>"""
        raise NotImplementedError

    return True


if __name__ == '__main__':
    # see for productionizing - https://stackoverflow.com/questions/51025893/flask-at-first-run-do-not-use-the-development-server-in-a-production-environmen
    app.run()