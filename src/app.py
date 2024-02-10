from flask import Flask, render_template
from threading import Thread
from flask_socketio import SocketIO
from gevent import monkey
from datetime import datetime, date, timedelta
from protected_dict import protected_dict as global_vars
from astral import LocationInfo
from astral.sun import sun
from dht22 import DHT22
from gpiozero import CPUTemperature
from door import DOOR
import time
import psutil
import pytz
import ruamel.yaml as YAML
import os.path
import board

##################################
# Flask configuration:
##################################

monkey.patch_all()
app = Flask(__name__, template_folder="../templates")
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app, async_mode='gevent')

##################################
# Helper functions:
##################################

# Get system uptime in seconds
uptime_seconds = psutil.boot_time()
uptime_datetime = datetime.fromtimestamp(uptime_seconds)

def get_uptime():
    # Calculate the time difference between now and the uptime
    uptime_delta = datetime.now() - uptime_datetime

    # Extract days, hours, minutes, and seconds from the time difference
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Return system uptime string
    return f"{days} day(s), {hours} hour(s), {minutes} minute(s), {seconds} second(s)"

# Define the location of Boulder, Colorado
boulder = LocationInfo("Boulder", "USA", "America/Denver", 40.01499, -105.27055)
timezone = pytz.timezone('America/Denver')

def get_sunrise_and_sunset():
    # Get the sunrise and sunset times for today
    s = sun(boulder.observer, date=date.today(), tzinfo=boulder.timezone)

    # Convert sunrise and sunset to the desired timezone (e.g., 'America/Denver')
    return s["sunrise"].astimezone(timezone), s["sunset"].astimezone(timezone)

config_filename = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "config.yaml")

def save_config():
    # Write the values to a YAML file
    with open(config_filename, 'w') as file:
        yaml = YAML.YAML()
        to_dump = {
            "auto_mode" : global_vars.instance().get_value("auto_mode"),
            "sunrise_offset" : global_vars.instance().get_value("sunrise_offset"),
            "sunset_offset" : global_vars.instance().get_value("sunset_offset")
        }
        yaml.dump(to_dump, file)

def load_config():
    ## Load the values from the YAML file
    config_to_set = {"auto_mode": True, "sunrise_offset": 0, "sunset_offset": 0}
    with open(config_filename, 'r') as file:
        yaml = YAML.YAML()
        content = file.read()
        yaml_config = yaml.load(content)
        config_to_set.update(yaml_config)
        global_vars.instance().set_values(config_to_set)

##################################
# Background tasks:
##################################

def temperature_task():
    dht_out = DHT22(board.D21)
    dht_in = DHT22(board.D20)
    while True:
        temp_out, hum_out = dht_out.get_temperature_and_humidity()
        temp_in, hum_in = dht_in.get_temperature_and_humidity()
        if temp_out is not None and hum_out is not None:
            print("Outside Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp_out, hum_out))
        if temp_in is not None and hum_in is not None:
            print("Inside Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp_in, hum_in))

        # Set global temperature and humidity:
        if temp_in is not None:
            global_vars.instance().set_value("temp_in", temp_in)
        if temp_out is not None:
            global_vars.instance().set_value("temp_out", temp_out)
        if hum_in is not None:
            global_vars.instance().set_value("hum_in", hum_in)
        if hum_out is not None:
            global_vars.instance().set_value("hum_out", hum_out)

        # Set CPU temperature:
        cpu_temp = CPUTemperature().temperature
        global_vars.instance().set_value("cpu_temp", cpu_temp)

        time.sleep(1.0)

# Background thread for managing coop door in real-time.
def door_task():
    door = DOOR()
    door_move_count = 0
    DOOR_MOVE_MAX = 35
    while True:
        # Get state and desired state:
        door_state = door.get_state()
        door_override = door.get_override()
        d_door_state, auto_mode = \
            global_vars.instance().get_values(["desired_door_state", "auto_mode"])

        # If we are in auto mode then open or close the door based on sunrise
        # or sunset times.
        if auto_mode:
            # Get the current sunrise and sunset time:
            sunrise, sunset = get_sunrise_and_sunset()
            current_time = timezone.localize(datetime.now())
            time_window = timedelta(minutes=1)

            # If we are in the 1 minute after sunrise, command the desired door
            # state to open.
            if current_time > sunrise and current_time < sunrise + time_window:
                global_vars.instance().set_value("desired_door_state", "open")

            # If we are in the 1 minute after sunset, command the desired door
            # state to closed.
            if current_time > sunset and current_time < sunset + time_window:
                global_vars.instance().set_value("desired_door_state", "closed")

        # Handle door:
        if door_override:
            # Set the desired state to stopped, so that
            # when override switch is no longer being used,
            # we don't move the motor until a new button is
            # pressed.
            global_vars.instance().set_value("desired_door_state", "stopped")
        elif door_state != d_door_state:
            match d_door_state:
                case "stopped":
                    if door_state in ["open", "closed"]:
                        door.stop(door_state)
                        door_move_count = 0
                    else:
                        door.stop()
                        door_move_count = 0
                case "open":
                    if door_move_count <= DOOR_MOVE_MAX:
                        door.open()
                        door_move_count += 1
                    else:
                        door.stop("open")
                        door_move_count = 0
                case "closed":
                    if door_move_count <= DOOR_MOVE_MAX:
                        door.close()
                        door_move_count += 1
                    else:
                        door.stop("closed")
                        door_move_count = 0
                case _:
                    door.stop()
                    door_move_count = 0
                    assert False, "Unknown state: " + str(d_door_state)
        else:
            door.stop(door_state)
            door_move_count = 0

        # Set global state
        door_state = door.get_state()
        door_override = door.get_override()
        global_vars.instance().set_values({ \
            "state": door_state, \
            "door_override": door_override, \
            "sunrise": sunrise, \
            "sunset": sunset \
        })
        time.sleep(1.0)

def data_update_task():
    while True:
        temp_in, hum_in, temp_out, hum_out, state, override, cpu_temp, \
            sunrise, sunset, auto_mode, sunrise_offset, sunset_offset = \
            global_vars.instance().get_values(["temp_in", "hum_in", \
                "temp_out", "hum_out", "state", "override", "cpu_temp", \
                "sunrise", "sunset", "auto_mode", "sunrise_offset", \
                "sunset_offset"])

        # Check if time until sunrise is positive
        time_until_open_str = None
        time_until_close_str = None
        if auto_mode == False:
            time_until_open_str = "disabled"
            time_until_close_str = "disabled"
        elif sunrise is not None and sunset is not None:
            # Assuming sunrise and sunset are datetime objects
            current_time = timezone.localize(datetime.now())
            time_until_open = sunrise + timedelta(minutes=sunrise_offset) - current_time
            time_until_close = sunset + timedelta(minutes=sunset_offset) - current_time

            if time_until_open > timedelta(0):
                time_until_open_str = (datetime.min + time_until_open).strftime("%H:%M:%S")
            else:
                time_until_open_str = "passed"

            # Check if time until sunset is positive
            if time_until_close > timedelta(0):
                time_until_close_str = (datetime.min + time_until_close).strftime("%H:%M:%S")
            else:
                time_until_close_str = "passed"

        to_send = {
          'temp_in': ("%0.1f" % temp_in) + u'\N{DEGREE SIGN}' + "F" if temp_in is not None else "",
          'hum_in': "%0.1f%%" % hum_in if hum_in is not None else "",
          'temp_out': ("%0.1f" % temp_out) + u'\N{DEGREE SIGN}' + "F" if temp_out is not None else "",
          'hum_out': "%0.1f%%" % hum_out if hum_out is not None else "",
          'cpu_temp': ("%0.1f" % cpu_temp ) + u'\N{DEGREE SIGN}' + "C" if cpu_temp is not None else "",
          'state': state if state is not None else "",
          'override': state if override else "off",
          'uptime': str(get_uptime()),
          'sunrise': sunrise.strftime("%-I:%M:%S %p") if sunrise is not None else "",
          'sunset': sunset.strftime("%-I:%M:%S %p") if sunset is not None else "",
          'tu_open': time_until_open_str if time_until_open_str is not None else "",
          'tu_close': time_until_close_str if time_until_close_str is not None else ""
        }
        socketio.emit('data', to_send)
        time.sleep(1.0)

##################################
# Websocket handlers:
##################################

@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(target=data_update_task)

@socketio.on('open')
def handle_open():
    print('Open button pressed')
    global_vars.instance().set_value("desired_door_state", "open")

@socketio.on('close')
def handle_close():
    print('Close button pressed')
    global_vars.instance().set_value("desired_door_state", "closed")

@socketio.on('stop')
def handle_stop():
    print('Stop button pressed')
    global_vars.instance().set_value("desired_door_state", "stopped")

@socketio.on('toggle')
def handle_toggle(message):
    toggle_value = message['toggle']
    if toggle_value:
        print('Auto Mode Enabled')
        global_vars.instance().set_value("auto_mode", True)
    else:
        global_vars.instance().set_value("auto_mode", False)
        print('Auto Mode Disabled')
    save_config()

@socketio.on('auto_offsets')
def handle_input_numbers(data):
    sunrise_offset = data['sunrise_offset']
    sunset_offset = data['sunset_offset']
    global_vars.instance().set_values({"sunrise_offset": int(sunrise_offset), "sunset_offset": int(sunset_offset)})
    save_config()

##################################
# Static page handlers:
##################################

# Route for the home page
@app.route('/')
def index():
    # Render the template with temperature and humidity values
    return render_template(
        'index.html',
        auto_mode=global_vars.instance().get_value("auto_mode"),
        sunrise_offset=global_vars.instance().get_value("sunrise_offset"),
        sunset_offset=global_vars.instance().get_value("sunset_offset")
    )

##################################
# Startup:
##################################

if __name__ == '__main__':
    # Initialize the desired door state:
    global_vars.instance().set_value("desired_door_state", "stopped")

    # Load global configuration file into memory
    load_config()

    # Start the task that manages the door:
    door_thread = Thread(target=door_task)
    door_thread.daemon = True
    door_thread.start()

    # Start the task that grabs temperature data:
    temp_thread = Thread(target=temperature_task)
    temp_thread.daemon = True
    temp_thread.start()

    # Start the Flask app
    socketio.run(app, debug=False, host='0.0.0.0')
