from data import IBKR

def pipeline():
    # initialize connection to IBKR
    client = IBKR()

    # download tradelog from IBKR (should do this once a day at end of trading day (exact time TBD))
    #client.query_flexreport('420983', savepath='scratch/data/interactive_brokers/test1.xml')

    # extract tradelog records into SQL Database (see data/models.py and data/schema.py for schema definitions)
    client.parse_tradelog('scratch/data/interactive_brokers/test1.xml', "data/sqlite.db")

pipeline()