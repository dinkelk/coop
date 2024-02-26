# Dinky Coop
*Those chickens won't open the door themselves...*

 |  ![`Coop App`](img/door.gif "door.gif") | 
 |:--:| 
 |  *Automatic door powered by linear actuator, video sped up 2.5x.* |


This is the [Raspberry Pi](https://www.raspberrypi.com) based controller software running my chicken coop. It exhibits the following capabilities:

  1. Automatic open and closing of coop door based on sunrise and sunset time (and configurable offset)
  2. Open and closing of the coop door via an external 3 position switch
  3. Temperature and humidity sensing inside and outside the coop
  4. Logging of all data to CSV files
  5. A simple [Flask](https://flask.palletsprojects.com/en) web app to view temperature and humidity and command the door

## The Web App

Below is the simple UI for the coop controller. It works well on a PC browser or phone.

 ![`Coop App`](img/app.png "app.png")

## How it is Wired Up

This is how things are connected, drawn using [Fritzing](https://fritzing.org/).

 ![`Coop Wiring Diagram`](img/coop_bb.svg "coop_bb.svg")

## How to Install

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

**Note:** Sometimes it is necessary to reset CircuitPython after encountering errors like `Unable to set line 21 to input` by running:

```
$ killall libgpiod_pulsein64
```

## Run Automatically at Startup

To start the controller automatically at boot, run `crontab -e` and append the following entry:

```
@reboot /home/pi/coop/cron_script.sh
```

## Future Improvements

  1. Show temperature/humidity plot of last 36 hours
