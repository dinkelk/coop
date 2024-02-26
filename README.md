# Dinky Coop
*Those chickens won't open the door themselves.*

 ![`Coop App`](img/door.gif "door.gif")

This is the [Raspberry Pi](https://www.raspberrypi.com) based controller software running my chicken coop. It currently exhibits the following capabilities:

  1. Automatic open and closing of coop door based on sunrise and sunset time (and configurable offset)
  2. Open and closing of the coop door via an external 3 position switch
  3. Temperature and humidity sensing inside and outside the coop
  4. A simple [Flask](https://flask.palletsprojects.com/en) web app using to view the current temperature and humidity and control the door
  5. Logging of all data to CSV files

 ![`Coop App`](img/app.png "app.png")

## How it is Wired Up

This is how things are connected, drawn using [Fritzing](https://fritzing.org/).

 ![`Coop Wiring Diagram`](img/coop_bb.svg "coop_bb.svg")

## How it is Run

On your Raspberry Pi, run the following:

```
$ git clone https://github.com/dinkelk/coop.git
$ cd coop
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements.txt
$ python3 src/app.py
```

Now access the webserver with a browser at http://127.0.0.1:5000.

Sometimes it is necessary to reset CircuitPython after errors like 'Unable to set line 21 to input' by running:

```
$ killall libgpiod_pulsein64
```

## Run Automatically at Startup

To start the controller automatically at boot, run `crontab -e` and append the following entry:

```
@reboot /home/pi/coop/cron_script.sh
```

## Future Improvements

  1. Show temp/humidity plot of last 36 hours
  2. Make webpage look nicer, photos, animations, icons
