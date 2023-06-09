from flask import Flask
from flask_login import LoginManager

from . import key
from . import views
from . import auth
from . import api


def create_app():
    app = Flask(__name__)
    # To run this program,
    # create file key.py and set it to
    # SECRET_KEY = 'YOUR SECRET KEY'
    # GOOGLE_CLIENT_ID = 'YOUR GOOGLE CLIENT ID'
    # GOOGLE_CLIENT_SECRET = 'YOUR GOOGLE CLIENT SECRET'
    app.config['SECRET_KEY'] = key.SECRET_KEY

    app.register_blueprint(views.views, url_prefix='/')
    app.register_blueprint(auth.auth, url_prefix='/')
    app.register_blueprint(api.api, url_prefix='/api/')
    lm = LoginManager()
    lm.login_view = 'auth.login'
    lm.init_app(app)

    @lm.user_loader
    def load_user(user_id):
        return auth.User.get(user_id)

    return app
