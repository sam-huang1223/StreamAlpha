import datetime

class Trade:
    def __init__(self, trade):        
        self.trade_type = trade.buySell
        self.security_type = trade.assetCategory
        self.currency = trade.currency
        self.fxRateToBase = float(trade.fxRateToBase)

        self.execution_time = datetime.datetime.strptime(str(trade.dateTime), '%Y%m%d;%H%M%S')
        self.settle_date = datetime.datetime.strptime(str(trade.settleDateTarget), '%Y%m%d').date()

        self.quantity = int(trade.quantity)

        #self.trade_id = trade.tradeID
        #self.transaction_id = trade.transactionID
        self.order_id = trade.ibOrderID

        self.commission = float(trade.ibCommission)

        self.price = float(trade.tradePrice)
        self.total = float(trade.tradeMoney)
        self.base_total = self.fxRateToBase * self.total

        self.total_cost_basis = float(trade.cost)
        self.pnl_realized = float(trade.fifoPnlRealized)

        if self.total_cost_basis == '':
            self.total_cost_basis = None
        if self.pnl_realized == '':
            self.pnl_realized = None

        if self.security_type == 'STK':
            self.security = Stock(trade)
        elif self.security_type == 'OPT':
            self.security = Option(trade)
        elif self.security_type == 'CASH':
            self.security = Cash(trade)
        else:
            raise ValueError("Instrument of type {} is not recognized".format(trade.assetCategory))

class Stock:
    def __init__(self, trade):
        self.ticker = trade.symbol
        self.description = trade.description
        self.ib_id = trade.conid
        self.isin = trade.isin
        self.exchange = trade.listingExchange

class Option:

    def __init__(self, trade):
        self.ib_id = trade.conid
        self.name = trade.description

        self.underlying = trade.underlyingSymbol
        self.underlying_ib_id = trade.underlyingConid
        self.underlying_isin = trade.underlyingSecurityID
        self.underlying_exchange = trade.underlyingListingExchange

        self.type = trade.putCall
        self.strike = trade.strike
        self.expiry = datetime.datetime.strptime(str(trade.expiry), '%Y%m%d').date()

class Cash:
    def __init__(self, trade):
        self.ib_id = trade.conid

        self.symbol = trade.symbol
        
        if trade.buySell == 'BUY':
            self.currency_to = trade.symbol.split('.')[0]
            self.currency_from = trade.symbol.split('.')[1]
        elif trade.buySell == 'SELL':
            self.currency_to = trade.symbol.split('.')[1]
            self.currency_from = trade.symbol.split('.')[0]

class Dividend:
    def __init__(self, dividend):
        self.dividend_id = dividend.symbol + ' ' + str(dividend.exDate)
        self.stock_id = dividend.symbol
        self.ex_date = datetime.datetime.strptime(str(dividend.exDate), '%Y%m%d').date()
        self.pay_date = datetime.datetime.strptime(str(dividend.payDate), '%Y%m%d').date()
        self.quantity = int(dividend.quantity)
        self.tax = float(dividend.tax)
        self.amount = float(dividend.grossRate)
        self.total = float(dividend.grossAmount)
        self.net_total = float(dividend.netAmount)
