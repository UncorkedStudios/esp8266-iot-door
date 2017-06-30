# IoT Door Signs

## Abstract

This is a project using an NodeMCU ESP8266, a Waveshare 4.3inch e-Paper display, and optionally a [PCB from electronictrik](https://www.tindie.com/products/electronictrik/high-tech-e-paper-iot-door-sign/) to create an Internet of Things door sign. This variation uses MicroPython on the ESP8266, Flask on a Raspberry PI, and the Google Calendar API.

## Bill of Materials

Here's what I used:

* [NodeMCU ESP8266 Development board](https://www.amazon.com/HiLetgo-Version-NodeMCU-Internet-Development/dp/B010O1G1ES)
* [Waveshare 4.3 e-Paper](http://www.waveshare.com/4.3inch-e-paper.htm)
* [High Tech E-paper IoT Door Sign PCB](https://www.tindie.com/products/electronictrik/high-tech-e-paper-iot-door-sign/) (Optional)
* [Raspberry PI 3 Model B](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/) (Optional)
* LiPoly charger (Optional)
* 2 SMD switches (Optional)
* 3.7v LiPoly battery (Optional)

## File List

```
display_project
  README.md
  - device
    display.py
    display_deep_sleep.py
    eink.py    (from dhallgb)
    secret.py    (you make this)
  - server
    + env
    app.py
    client_secret.json    (from Google)
    helpers.py
    requirements.txt
    rooms.py    (you make this)
```

## Getting MicroPython on the ESP8266

First you'll want to download a few things:

* [MicroPython for the ESP8266](http://micropython.org/download#esp8266) (recent stable build)
* [e-Ink Library for MicroPython](https://github.com/dhallgb/eInk-micropython)
* [Custom Project Files](https://github.com/UncorkedStudios/esp8266-iot-door)

The device side of things has a few dependencies:

* [pip](https://pip.pypa.io/en/stable/installing/): Python package management
* [esptool](https://pypi.python.org/pypi/esptool): For flashing the ESP firmware
* [ampy](https://github.com/adafruit/ampy): For managing files on the ESP

To determine the path to your ESP8266, start with it unplugged and run this in your terminal:

``` shell
ls /dev
```

Now plug in your ESP8266 and run the `ls /dev` command again. You should see something new - for me the path to my ESP is `/dev/tty.SLAB_USBtoUART`. Now let's flash the firmware (you'll need to replace the path to your device and the path to the firmware):

``` shell
pip install esptool
esptool.py --port /dev/tty.SLAB_USBtoUART erase_flash
esptool.py --port /dev/tty.SLAB_USBtoUART --baud 115200 write_flash --flash_size=detect 0 esp8266-20170526-v1.9.bin
```

If you run into any issues, you may need to adjust the baud rate and make sure you're getting enough power to the ESP8266 (I had to use a powered USB hub for this). If you're still having issues, try these steps:

* Start with the ESP8266 unpowered
* Hold down the `FLASH` button
* While holding down the button, plug in the ESP8266
* While continuing to hold the button down, run the above `esptool.py` commands
* When `esptool.py` connects, release the button

Now's a good time to create a `secret.py` file for your ESP8266:

``` Python
# secret.py
WIFI_SSID = '<YOUR WIFI NETWORK>'
WIFI_PASS = '<YOUR WIFI PASSWORD>'
SERVER_ADDRESS = '<THE FLASK SERVER>'
```

## Getting Python Files to the ESP8266

Now we're going to get the files on the ESP using ampy. The files we need are:

* `display.py` or `display_deep_sleep.py`: this is my custom script for displaying room information
* `eink.py`: this is the e-ink library by dhallgb
* `secret.py`: this is the file you created above

The `display.py` file will be renamed `main.py` so that it gets run after booting:

``` shell
pip install adafruit-ampy
ampy --port /dev/tty.SLAB_USBtoUART put display.py /main.py
ampy --port /dev/tty.SLAB_USBtoUART put eink.py
ampy --port /dev/tty.SLAB_USBtoUART put secret.py
```

When we restart the ESP, it will run `/main.py` and begin checking in with the Flask server. Realize that `display.py` will need to be modified according to your needs (same with the Flask server).

If you need to troubleshoot at this point, you may want to try booting with dhallgb's `demo.py` file:

``` shell
ampy --port /dev/tty.SLAB_USBtoUART put demo.py /main.py
```

When you boot, you should see some fun displays. The demo is a good place to start to see how the e-Ink library works.

## Setting Up the Flask Server

I'm not going to get too bogged down in documenting Google's API - their API is already well documented. Here are some resources to lead the way though:

* [Google API Authentication](https://developers.google.com/api-client-library/python/guide/aaa_overview)
* [Google API Python Quickstart](https://developers.google.com/admin-sdk/directory/v1/quickstart/python)

The second link will walk you through getting your `client_secret.json`. Then you'll need a room directory so the Flask server can translate room names to calendarIds:

``` Python
# rooms.py
rooms = {
  'moss': '<GOOGLE CALENDARID>',
}
```

With the Google stuff and a directory of rooms, we should be all set to start the Flask server. We're going to do this in a virtual environment per Flask's suggestion:

``` shell
virtualenv env
source env/bin/activate
pip install -r requirements.txt
python app.py
```

The first time you do this, you'll be asked to login to your Google account via a browser popup. Google's code in `helpers.py` will save the credentials so that you won't be asked again in the future.

## Some Code to Change

My code probably isn't going to work for you unless you have a room named Moss. Besides making `secret.py`, `rooms.py`, and getting `client_secret.json`, you'll probably want to change a few things:

``` Python
# Timezones may need to be updated

# helpers.py
now = datetime.datetime.now(pytz.timezone("US/Pacific")).isoformat()
# app.py
res['todays_date'] = datetime.datetime.now(pytz.timezone("US/Pacific")).strftime('%-m/%-d')
```

``` Python
# Each ESP8266 will need to be assigned a room name

# display.py
ROOM_NAME = 'moss'
```

## Wrap Up

The ESP8266 reaches out to the Flask server via something like `GET http://192.168.1.1/moss`, the Flask server takes the parameter and converts it to the Google CalendarId, a request for the next three events of the day for that room is made with the Google Calendar Resource API, the Flask server formats the response before handing a small JSON file to the ESP8266, and then the ESP8266 displays the data.

It's recommended that you don't rely on the Flask development server in production. For my prototyping needs it worked (mostly) fine, but a live launch will probably need something like Gunicorn and Nginx.

The battery life isn't ideal, which is why I'm working on `display_deep_sleep.py` to put the ESP8266 into deep sleep in between API calls.

Thanks for looking!
