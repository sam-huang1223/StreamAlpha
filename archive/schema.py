# package imports
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineConnectionField, MongoengineObjectType

# local imports
import models

class Stock(MongoengineObjectType):

    class Meta:
        model = models.Stock
        interfaces = (Node,)

class Option(MongoengineObjectType):

    class Meta:
        model = models.Option
        interfaces = (Node,)

### Mutations
class StockInput(graphene.InputObjectType):
    ID = graphene.String()
    ticker = graphene.String()

class updateStock(graphene.Mutation):
    stock = graphene.Field(Stock)

    class Arguments:
        stock_data = StockInput(required=True)

    def mutate(self, info, stock_data):
        stock = models.Stock.objects.get(pk=stock_data.ticker)
        if stock_data.ID:
            stock.ID = stock_data.ID

        stock.save()

        return updateStock(stock=stock)

class Mutations(graphene.ObjectType):
    updateStock = updateStock.Field()

### Queries
class Queries(graphene.ObjectType):
    stocks = MongoengineConnectionField(Stock)   # maps to stocks collection
    options = MongoengineConnectionField(Option)

    # 1 line per collection

schema = graphene.Schema(query=Queries, mutation=Mutations, types=[Stock, Option])