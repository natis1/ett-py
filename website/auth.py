from flask import Blueprint, render_template, request, flash, redirect
from flask_login import current_user, login_user, UserMixin, login_required, logout_user
from oauthlib.oauth2 import WebApplicationClient
from . import key
import requests
import json
from src import database

auth = Blueprint('auth', __name__)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(key.GOOGLE_CLIENT_ID)


class User(UserMixin):
    def __init__(self, user_id, name, permissions):
        self.id = user_id
        self.name = name
        self.permissions = permissions

    def is_anonymous(self):
        return False

    def is_active(self):
        return self.permissions > 0

    @staticmethod
    def get(user_id):
        row = database.get_row("historians", "OathID", user_id)
        if row is None:
            return None
        return User(row[0], row[2], row[3])


@auth.route('/login', methods=['GET'])
def login():
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    # noinspection PyNoneFunctionAssignment
    redirect_url = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email"],
    )
    return redirect(redirect_url)


@auth.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    if code is None:
        return 'Invalid authentication request!', 400
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(key.GOOGLE_CLIENT_ID, key.GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        print(unique_id, users_email)
        print(type(unique_id))
        user = User.get(unique_id)
        if user is None:
            flash("You are not an authorized historian. Your unique ID is: " + unique_id, 'error')
            return redirect("/sign-up")
        else:
            login_user(user, remember=False)
            flash("You are now logged into the ETT database", 'success')
            return redirect("/")

    else:
        flash("User email not available or not verified by Google.", 'error')
        return redirect('/')


# @auth.route('/login', methods=['POST'])
# def login_post():
#    data = request.form
#    print(data)
#    return render_template("login.html")


@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect('/')


@auth.route('/sign-up', methods=['GET'])
def sign_up():
    if current_user.is_authenticated:
        return 'You are already logged in!', 400
    return render_template("sign_up.html", user=current_user)

