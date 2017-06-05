
from __future__ import print_function
import datetime
import httplib2
import os
import re
import time
import pytz

# Google stuff
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# Takes Google time and return an tuple with a date string and a time string
# Input ex: '2017-12-25T08:00:00-07:00'
# Output ex: ('12/25', '8:00am')
def process_time(google_time):
    # Grab elements from Google time
    t = time.strptime(str(google_time), "%Y-%m-%dT%H:%M:%S-07:00")
    # Format date
    result_date = "{}/{}".format(t[1], t[2])
    # Convert 24-hour to 12-hour time
    hour = int(t[3])
    setting = "am"
    if hour > 12:
        hour -= 12
        setting = "pm"
    # Format time
    result_time = "{}:{:02d}{}".format(hour, t[4], setting)
    return result_date, result_time

# Gets valid user credentials from storage.
# If nothing has been stored, or if the stored credentials are invalid,
# the OAuth2 flow is completed to obtain the new credentials.
# Returns:
#     Credentials, the obtained credential.
#
# Google stores all of this stuff at ~/.credentials
def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    # This line will probably change if you name your Google stuff something different
    credential_path = os.path.join(credential_dir, 'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', 'https://www.googleapis.com/auth/calendar.readonly')
        # This line will probably change if you name your Google stuff something different
        flow.user_agent = 'Google Calendar API Python Quickstart'
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

# credentials are the results from get_credentials()
# calendar_id is the unique identifier of the room
# Returns array of the upcoming events for the day (up to 3) or an empty array
def get_events(credentials, calendar_id):
    # Do Google things
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    # datetime for the current time (Pacific Time)
    now = datetime.datetime.now(pytz.timezone("US/Pacific")).isoformat()
    # datetime for end of day
    later = re.sub('\d{2}:\d{2}:\d{2}', '23:59:59', now)
    # Get upcoming events for room,
    # between now time and later time
    # a maximum of three entries
    eventsResult = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=later,
        maxResults=3,
        singleEvents=True,
        orderBy='startTime'
        ).execute()
    events = eventsResult.get('items', [])
    return format_event_array(events)

# Takes the Google API response and formats it for our device
# Returns an array of events dicts or empty array
# [{
#     'start_date': '10/03',
#     'start_time': '6:30pm',
#     'end_date': '10/03',
#     'end_time': '7:00pm',
#     'summary': 'This is a big event!',
#     'time_display': '6:30pm-7:00pm',
#     'long_display': '6:30pm-7:00pm This is a big event!'
# }]
def format_event_array(events):
    results = []
    for event in events:
        event_obj = {}
        event_obj['start_date'], event_obj['start_time'] = process_time(event['start']['dateTime'])
        event_obj['end_date'], event_obj['end_time']     = process_time(event['end']['dateTime'])
        event_obj['summary'] = event['summary']
        event_obj['time_display'] = "{}-{}".format(event_obj['start_time'], event_obj['end_time'])
        event_obj['long_display'] = "{}-{} {}".format(event_obj['start_time'], event_obj['end_time'], event_obj['summary'])
        results.append(event_obj)
    return results
