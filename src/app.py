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
app = Flask(__name__, template_folder="templates")
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

def get_current_time():
    return timezone.localize(datetime.now())

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
config_filename = os.path.join(root_path, "config.yaml")

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

def get_all_data():
    # Grab data safely from global store:
    temp_in, hum_in, temp_out, hum_out, state, override, cpu_temp, \
        sunrise, sunset, auto_mode, sunrise_offset, sunset_offset, \
        temp_in_min, temp_in_max, hum_in_min, hum_in_max, \
        temp_out_min, temp_out_max, hum_out_min, hum_out_max, \
        cpu_temp_min, cpu_temp_max \
        = global_vars.instance().get_values(["temp_in", "hum_in", \
            "temp_out", "hum_out", "state", "override", "cpu_temp", \
            "sunrise", "sunset", "auto_mode", "sunrise_offset", "sunset_offset", \
            "temp_in_min", "temp_in_max", "hum_in_min", "hum_in_max", \
            "temp_out_min", "temp_out_max", "hum_out_min", "hum_out_max", \
            "cpu_temp_min", "cpu_temp_max"])

    # Check if time until sunrise is positive
    time_until_open_str = None
    time_until_close_str = None
    if auto_mode == False:
        time_until_open_str = "disabled"
        time_until_close_str = "disabled"
    elif sunrise is not None and sunset is not None:
        # Assuming sunrise and sunset are datetime objects
        current_time = get_current_time()
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

    def format_temp(temp, units="F"):
        return ("%0.1f" % temp) + u'\N{DEGREE SIGN}' + units if temp is not None else ""

    def format_hum(hum):
        return "%0.1f%%" % hum if hum is not None else ""

    # Return nicely formatted data in dictionary form:
    data_dict = {
      'temp_in': format_temp(temp_in),
      'temp_in_min': format_temp(temp_in_min),
      'temp_in_max': format_temp(temp_in_max),
      'hum_in': format_hum(hum_in),
      'hum_in_min': format_hum(hum_in_min),
      'hum_in_max': format_hum(hum_in_max),
      'temp_out': format_temp(temp_out),
      'temp_out_min': format_temp(temp_out_min),
      'temp_out_max': format_temp(temp_out_max),
      'hum_out': format_hum(hum_out),
      'hum_out_min': format_hum(hum_out_min),
      'hum_out_max': format_hum(hum_out_max),
      'cpu_temp': format_temp(cpu_temp, units="C"),
      'cpu_temp_min': format_temp(cpu_temp_min, units="C"),
      'cpu_temp_max': format_temp(cpu_temp_max, units="C"),
      'state': state if state is not None else "",
      'override': state if state is not None and override else "off",
      'uptime': str(get_uptime()),
      'sunrise': sunrise.strftime("%-I:%M:%S %p") if sunrise is not None else "",
      'sunset': sunset.strftime("%-I:%M:%S %p") if sunset is not None else "",
      'tu_open': time_until_open_str if time_until_open_str is not None else "",
      'tu_close': time_until_close_str if time_until_close_str is not None else ""
    }
    return data_dict

##################################
# Background tasks:
##################################

def temperature_task():
    dht_out = DHT22(board.D21)
    dht_in = DHT22(board.D16)
    last_date = None

    # Update value in global vars, and also store min and max seen since startup:
    def update_val(val, name):
        if val is not None:
            val_max, val_min = global_vars.instance().get_values([name + "_max", name + "_min"])
            val_max = val_max if val_max is not None else -500
            val_min = val_min if val_min is not None else 500
            if val > val_max:
                val_max = val
            if val < val_min:
                val_min = val
            global_vars.instance().set_values({name: val, name + "_max": val_max, name + "_min": val_min})

    while True:
        temp_out, hum_out = dht_out.get_temperature_and_humidity()
        temp_in, hum_in = dht_in.get_temperature_and_humidity()

        #if temp_out is not None and hum_out is not None:
        #    print("Outside Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp_out, hum_out))
        #if temp_in is not None and hum_in is not None:
        #    print("Inside Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp_in, hum_in))

        # If it is midnight then reset the mins and maxes so we get fresh values for the new day:
        current_date = date.today()
        if current_date != last_date:
            global_vars.instance().set_values({ \
                "temp_in_min": 500, "temp_in_max": -500, \
                "temp_out_min": 500, "temp_out_max": -500, \
                "hum_in_min": 500, "hum_in_max": -500, \
                "hum_out_min": 500, "hum_out_max": -500, \
                "cpu_temp_min": 500, "cpu_temp_max": -500 \
            })
            last_date = current_date

        # Update the global variables for all the temperatures:
        update_val(temp_in, "temp_in")
        update_val(hum_in, "hum_in")
        update_val(temp_out, "temp_out")
        update_val(hum_out, "hum_out")

        # Set CPU temperature:
        cpu_temp = CPUTemperature().temperature
        update_val(cpu_temp, "cpu_temp")

        time.sleep(2.5)

# Background thread for managing coop door in real-time.
def door_task():
    door = DOOR()
    door_move_count = 0
    DOOR_MOVE_MAX = 35 # seconds
    first_iter = True
    while True:
        # Get state and desired state:
        door_state = door.get_state()
        door_override = door.get_override()
        d_door_state, auto_mode = \
            global_vars.instance().get_values(["desired_door_state", "auto_mode"])

        # If we are in auto mode then open or close the door based on sunrise
        # or sunset times.
        if auto_mode:
            # Get the current sunrise and sunset time, time of close, time of open, and current time.
            sunrise, sunset = get_sunrise_and_sunset()
            sunrise_offset, sunset_offset = global_vars.instance().get_values(["sunrise_offset", "sunset_offset"])
            open_time = sunrise + timedelta(minutes=sunrise_offset)
            close_time = sunset + timedelta(minutes=sunset_offset)
            current_time = get_current_time()
            time_window = timedelta(minutes=1)

            # If we just booted up, then we need to make sure the door is in the
            # correct position. This prevents the door from being stuck in the wrong
            # position due to an unfortunately timed power outage.
            if first_iter:
                if current_time >= open_time and current_time < close_time:
                    global_vars.instance().set_value("desired_door_state", "open")
                else:
                    global_vars.instance().set_value("desired_door_state", "closed")

            # If we are in the 1 minute after sunrise, command the desired door
            # state to open.
            if current_time >= open_time and current_time <= open_time + time_window:
                global_vars.instance().set_value("desired_door_state", "open")

            # If we are in the 1 minute after sunset, command the desired door
            # state to closed.
            if current_time >= close_time and current_time <= close_time + time_window:
                global_vars.instance().set_value("desired_door_state", "closed")

        # If we are in override mode, then the door is being moved by the switch.
        if door_override:
            # See if switch is turned off, if so, stop the door.
            door.check_if_switch_neutral()

            # Set the desired state to stopped, so that
            # when override switch is no longer being used,
            # we don't move the motor until a new button is
            # pressed.
            global_vars.instance().set_value("desired_door_state", "stopped")

        # If the door state does not match the desired door state, then
        # we need to move the door.
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

        # We are not in switch override, and the door is in the desired state. The door should be
        # stopped. We can do this most robustly by also checking the switch, which will stop the door
        # as long as it is in the nuetral position. This helps us catch a switch close or open that
        # sometimes gets missed by the edge detection.
        else:
            # Check if switch off, if so, stop the door.
            door.check_if_switch_neutral(nuetral_state=door.get_state())
            door_move_count = 0

        # Set global state
        first_iter = False
        door_state = door.get_state()
        door_override = door.get_override()
        global_vars.instance().set_values({ \
            "state": door_state, \
            "override": door_override, \
            "sunrise": sunrise, \
            "sunset": sunset \
        })
        time.sleep(1.0)

def data_update_task():
    while True:
        to_send = get_all_data()
        socketio.emit('data', to_send)
        time.sleep(1.0)

def data_log_task():
    # Form log file name in form log/YY_MM_DD.csv
    def get_log_file_name():
        current_date = datetime.now()
        formatted_date = current_date.strftime("%Y_%m_%d")
        return os.path.join(os.path.join(root_path, "log"), formatted_date + ".csv")

    # Make log directory:
    log_dir = os.path.dirname(get_log_file_name())
    os.makedirs(log_dir, exist_ok=True)

    last_log_file_name = ""
    while True:
        data = get_all_data()

        # Open new log file and write CSV header if it is a new day
        log_file_name = get_log_file_name()
        if log_file_name != last_log_file_name:
            with open(log_file_name, 'a') as file:
                header = "# " + ", ".join(data.keys()) + "\n"
                file.write(header)

        # Append data to file:
        with open(log_file_name, 'a') as file:
            row = ", ".join(data.values()) + "\n"
            file.write(row)

        # Sleep a bit:
        last_log_file_name = log_file_name
        time.sleep(5.0)

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

    # Start the task that logs data to CSV files:
    log_thread = Thread(target=data_log_task)
    log_thread.daemon = True
    log_thread.start()

    # Start the Flask app
    socketio.run(app, debug=False, host='0.0.0.0')
