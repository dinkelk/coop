# Dinky Coop
*Those chickens won't open the door themselves.*

This is the Raspberry Pi based controller software running my chicken coop. It currently exhibits the following capabilities:

  1. Automatic open and closing of coop door based on sunrise and sunset time
  2. Open and closing of the coop door via 3 position switch
  3. Temperature and humidity sensing inside and outside the coop
  4. A simple web app to view the current temperature and humidity and control the door

## How it is Wired Up

 ![`Coop Wiring Diagram`](img/coop_bb.svg "coop_bb.svg")

## How it is Run

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
# This is sometimes necessary to reset
# CircuitPython after errors like 'Unable to set line 21 to input'.
$ killall libgpiod_pulsein64
$ flask src/app.py
```

## TODO

  1. Sunrise / sunset offsets
  2. Log data to file, one file per day
  3. Show daily max and min temperature and humidity (min (blue), current (black), max (orange))
  4. Show temp/humidity plot of last 36 hours
  5. Make webpage look nicer, photos, animations, icons
