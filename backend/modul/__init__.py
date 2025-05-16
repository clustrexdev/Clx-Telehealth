from flask import Flask
from flask_cors import CORS
import json
import serverless_wsgi
from modul.vonage import register_routes
from modul.athena_endpoints import register_athena_routes

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Home page"

register_routes(app=app)

register_athena_routes(app=app)

# Comment the handler while testing in local development.
def handler(event, context):
    print("Event:", json.dumps(event))
    return serverless_wsgi.handle_request(app, event, context)

