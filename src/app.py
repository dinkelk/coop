from flask import Flask, render_template
from threading import Thread, Lock
from flask_socketio import SocketIO, emit
import time
import subprocess
from gevent import monkey
from datetime import datetime

monkey.patch_all()

app = Flask(__name__, template_folder="../templates")
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app, async_mode='gevent')

def get_linux_uptime():
    output = subprocess.check_output('uptime -s', shell=True)
    uptime = output.decode().strip()
    return uptime

# Global variables to store data for page:
global_temperature = None
global_humidity = None
global_cpu_temp = None
global_door_state = None
global_door_override = False
global_desired_door_state = "stopped"
lock = Lock()

def temperature_task():
    import board
    from dht22 import DHT22
    from gpiozero import CPUTemperature
    global global_temperature, global_humidity, global_cpu_temp
    dht = DHT22(board.D21)
    while True:
        temp, hum = dht.get_temperature_and_humidity()
        if temp is not None and hum is not None:
            print("Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp, hum))

        # Set global temperature and humidity:
        if temp is not None:
            with lock:
                global_temperature = temp

        if hum is not None:
            with lock:
                global_humidity = hum

        cpu_temp = CPUTemperature().temperature
        with lock:
            global_cpu_temp = cpu_temp

        time.sleep(1.0)

# Background thread for managing coop in real-time.
def background():
    from door import DOOR
    global global_door_state, global_desired_door_state, global_door_override

    door = DOOR()
    door_move_count = 0
    DOOR_MOVE_MAX = 20
    while True:
        # Get state and desired state:
        door_state = door.get_state()
        door_override = door.get_override()
        with lock:
            d_door_state = global_desired_door_state

        # Handle door
        if door_override:
            # Set the desired state to stopped, so that
            # when override switch is no longer being used,
            # we don't move the motor until a new button is
            # pressed.
            with lock:
                global_desired_door_state = "stopped"
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
        with lock:
            global_door_state = door_state
            global_door_override = door_override

        time.sleep(1.0)

@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(target=update_data)

@socketio.on('open')
def handle_open():
    print('Open button pressed')
    global global_desired_door_state
    with lock:
        global_desired_door_state = "open"

@socketio.on('close')
def handle_close():
    print('Close button pressed')
    global global_desired_door_state
    with lock:
        global_desired_door_state = "closed"

@socketio.on('stop')
def handle_close():
    print('Stop button pressed')
    global global_desired_door_state
    with lock:
        global_desired_door_state = "stopped"

def update_data():
    while True:
        with lock:
            temp = global_temperature
            hum = global_humidity
            state = global_door_state
            override = global_door_override
            cpu_temp = global_cpu_temp
        to_send = {
          'temp': ("%0.1f" % temp) + u'\N{DEGREE SIGN}' + "F" if temp is not None else "",
          'hum': "%0.1f%%" % hum if hum is not None else "",
          'cpu_temp': ("%0.1f" % cpu_temp ) + u'\N{DEGREE SIGN}' + "C" if cpu_temp is not None else "",
          'state': state if state is not None else "",
          'override': state if override else "off",
          'curtime': str(datetime.now())
        }
        socketio.emit('data', to_send)
        time.sleep(1.0)

# Route for the home page
@app.route('/')
def index():
    # Render the template with temperature and humidity values
    return render_template(
        'index.html',
        uptime=get_linux_uptime(),
    )

if __name__ == '__main__':
    # Start the background thread
    thread = Thread(target=background)
    thread.daemon = True
    thread.start()

    thread2 = Thread(target=temperature_task)
    thread2.daemon = True
    thread2.start()

    # Start the Flask app
    socketio.run(app, debug=False, host='0.0.0.0')
