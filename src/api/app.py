# package imports
from flask import Flask
from flask_graphql import GraphQLView

# local imports
from database import init_db
from schema import schema


app = Flask(__name__)
app.debug = True

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
)

if __name__ == '__main__':
    init_db()
    app.run()