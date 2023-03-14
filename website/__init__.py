from flask import Flask
from . import key
from . import views
from . import auth


def create_app():
    app = Flask(__name__)
    # To run this program,
    # create file key.py and set it to
    # SECRET_KEY = 'YOUR SECRET KEY'
    app.config['SECRET_KEY'] = key.SECRET_KEY

    app.register_blueprint(views.views, url_prefix='/')
    app.register_blueprint(auth.auth, url_prefix='/')

    return app
