# package imports
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineConnectionField, MongoengineObjectType

# local imports
from models import Stock as StockModel


class Stock(MongoengineObjectType):

    class Meta:
        model = StockModel
        interfaces = (Node,)


class Query(graphene.ObjectType):
    node = Node.Field()
    all_stocks = MongoengineConnectionField(Stock)   # maps to allStocks

schema = graphene.Schema(query=Query, types=[Stock])