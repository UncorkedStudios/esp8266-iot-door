import datetime
from flask import Flask, jsonify

# Dict of rooms to store calendarIds
from rooms import rooms
# Custom helper functions
from helpers import *

# Initialize Flask app
app = Flask(__name__)
# Store Google credentials
credentials = get_credentials()

@app.route('/<room_name>')
def index(room_name):
    res = {}
    # General information
    res['todays_date'] = datetime.datetime.now(pytz.timezone("US/Pacific")).strftime('%-m/%-d')
    res['room_name'] = room_name.title()
    # Array of event dicts
    # for the next three events scheduled for the room
    res['events'] = get_events(credentials, rooms[room_name.lower()])
    return jsonify(res)

if __name__ == '__main__':
    # Make the Flask app accessible to all
    app.run(host='0.0.0.0')
