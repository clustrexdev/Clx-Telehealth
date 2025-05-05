from flask import Flask, Blueprint
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
app.register_blueprint(Blueprint('appname', __name__))


@app.route("/")
def home():
    return "Home page"

from module import vonage
from module import athena_endpoints
