import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

API_TOKEN = ""
RSA_KEY = ""
app = Flask(__name__)

def weather_main(location, date):
    url_base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    url = (
        f"{url_base_url}/{location}/{date}"
        f"?unitGroup=metric"
        f"&key={RSA_KEY}"
        f"&contentType=json"
    )
    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        print(response.text)
    else:
        print("Error:", response.status_code, response.text)

    return json.loads(response.text)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/")
def home_page():
    return "<p><h2>KMA L2: python Saas weather.</h2></p>"

@app.route(
    "/content/api/v1/integration/generate",
    methods=["POST"],
)
def weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    requester_name = json_data.get("requester_name")
    location = json_data.get("location")
    date = json_data.get("date")

    if not requester_name or not location or not date:
        raise InvalidUsage("requester_name, location, and date are required", status_code=400)

    weather = weather_main(location, date)
    day = weather['days'][0]

    weather_need = {
        "temp_c": day.get('temp'),
        "feels_like_c": day.get('feelslike'),
        "wind_kph": day.get('windspeed'),
        "pressure_mb": day.get('pressure'),
        "humidity": day.get('humidity'),
        "visibility": day.get('visibility')
    }

    result = {
        "requester_name": requester_name,
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "date": date,
        "weather": weather_need
    }

    return jsonify(result)
