# coop
*Those chickens won't open the door themselves.*

## How to Run

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
# This is sometimes necessary to reset
# CircuitPython after errors like 'Unable to set line 21 to input'.
$ killall libgpiod_pulsein64
$ flask src/app.py
```
