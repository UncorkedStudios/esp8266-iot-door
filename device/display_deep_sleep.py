#!/usr/bin/env python
from eink import *
from time import sleep
import machine
import network
import urequests

# Import secret things: WiFi credentials and Raspberry Pi server address
# All just normal strings
from secret import WIFI_SSID, WIFI_PASS, SERVER_ADDRESS

# Room name will be unique for each ESP8266
ROOM_NAME = 'oak'
ROOM_DATA = {}

def display_data():
    # Use the global ROOM_DATA
    # rather than create a new local variable
    global ROOM_DATA

    try:
        # Get data from Raspberry Pi
        req = urequests.get('{}/{}'.format(SERVER_ADDRESS, ROOM_NAME))
        # Grab JSON from response
        data = req.json()
        # If response is different from ROOM_DATA,
        # update ROOM_DATA and display it
        if data != ROOM_DATA:
            ROOM_DATA = data
            room_display(ROOM_DATA)
        # Close request
        req.close()
    except Exception:
        # If error, do nothing
        pass

    # Deep sleep for a minute
    deep_sleep(60000)

def deep_sleep(sleep_length):
    # To preserve power, we'll go into deep sleep between API calls
    # configure RTC.ALARM0 to be able to wake the device
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)

    # set RTC.ALARM0 to fire after 10 seconds (waking the device)
    rtc.alarm(rtc.ALARM0, sleep_length)

    # put the device to sleep
    machine.deepsleep()

def room_display(room):
    eink_clear()
    # Display room name
    eink_set_en_font(ASCII64)
    eink_disp_string(room['room_name'], 50, 50)
    # Display date
    eink_set_en_font(ASCII48)
    eink_disp_string(room['todays_date'], 50, 125)
    # Display the next scheduled room event if it exists
    event_length = len(room['events'])
    if event_length > 0:
        eink_disp_string(room['events'][0]['summary'], 50, 225)
        eink_disp_string(room['events'][0]['time_display'], 50, 300)
    # Display the following two scheduled room events if they exists
    if event_length > 1:
        eink_set_en_font(ASCII32)
        position = 425
        for event in room['events'][1:]:
            eink_disp_string(event['long_display'], 50, position)
            position += 50
    # Display the things
    eink_update()

# Display a flash of text for "leng" seconds
def text_flash(text, leng=5):
    eink_clear()
    eink_set_en_font(ASCII64)
    eink_disp_string(text, 100, 250)
    eink_update()
    sleep(leng)

def wifi_connect():
    try:
        # Set device as WiFi station
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            # Connect to WiFi
            wlan.connect(WIFI_SSID, WIFI_PASS)
            while not wlan.isconnected():
                pass
        # Display network name
        # text_flash(WIFI_SSID)
    except Exception:
        text_flash("Unable to connect to WiFi")

# Initilize Waveshare display
Tx = 'G12'
Rx = 'G13'
eink_init()
eink_set_color(BLACK, WHITE)

# Initilize ESP8266
# text_flash('Connecting to WiFi...')
wifi_connect()

# Start displaying things
display_data()
