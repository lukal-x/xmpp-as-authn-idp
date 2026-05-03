from flask import Flask, current_app, redirect, request, session
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
import marshmallow as ma

import base64
import json

from bosh import Bosh, Client

JABBER_SERVER = "unexposed-jabber"

root = Blueprint("root", __name__, url_prefix="", description="Application root")


@root.route("/")
class Root(MethodView):

    @root.response(200)
    def get(self):
        who = "world"

        if "username" in session:
            who = session["username"]

        return f"hello {who}!"


authn = Blueprint("authn", __name__, description="Authentication")


class Credentials(ma.Schema):
    username = ma.fields.String(required=True)
    password = ma.fields.String(required=True)


@authn.route("/authn")
class Authn(MethodView):

    @authn.arguments(Credentials)
    @authn.response(200)
    def post(self, creds: Credentials):
        error: str | None = current_app.config["BOSH"].login(
            creds["username"], creds["password"]
        )

        if error is not None:
            abort(500, message=error)

        session["username"] = creds["username"]

        return redirect("/")


app = Flask(__name__)
app.secret_key = "qwertyuiop"
app.config["API_TITLE"] = "XMPP authn example"
app.config["API_VERSION"] = "v0.0.1"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)

api.register_blueprint(root)
api.register_blueprint(authn)


if __name__ == "__main__":
    client = Client.create(JABBER_SERVER, 5280)
    app.config["BOSH"] = Bosh.greet(client)
    app.run(host="0.0.0.0", port=5005)
