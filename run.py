from data import IBKR

client = IBKR()
#client.query_flexreport('420983', savepath='temp/data/interactive_brokers/test1.xml')
client.play()