from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from flask_graphql import GraphQLView


# app initialization
app = Flask(__name__)

# Configs
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# SQLAlchemy DataBase Initialization
db = SQLAlchemy(app)


# Models
class User(db.Model):
    uuid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), index=True, unique=True)
    posts = db.relationship('Post', backref='author')

    def __repr__(self):
        return '<User %r>' % self.username


class Post(db.Model):
    uuid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), index=True)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.uuid'))

    def __repr__(self):
        return '<Post %r>' % self.title


db.create_all()


"""
john = User(username='john2')

post1 = Post()
post1.title = "Hello World"
post1.body = "This is the first post"
post1.author = john

post2 = Post()
post2.title = "Hello World"
post2.body = "This is the second post"
post2.author = john
db.session.add(post1)
db.session.add(post2)
db.session.add(john)
db.session.commit()
"""


# Schema Objects
class PostObject(SQLAlchemyObjectType):
    class Meta:
        model = Post
        interfaces = (graphene.relay.Node,)


class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_posts = SQLAlchemyConnectionField(PostObject)
    all_users = SQLAlchemyConnectionField(UserObject)


schema = graphene.Schema(query=Query)


# Mutation (For adding rows)
# Schema Objects
class CreatePost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        body = graphene.String(required=True)
        username = graphene.String(required=True)
    post = graphene.Field(lambda: PostObject)

    def mutate(self, info, title, body, username):
        user = User.query.filter_by(username=username).first()
        post = Post(title=title, body=body)
        if user is not None:
            post.author = user
        db.session.add(post)
        db.session.commit()
        return CreatePost(post=post)


class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)


# Routes
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))




@app.route('/')
def index():
    return 'Hello World'


if __name__ == '__main__':
    app.run(debug=True)
