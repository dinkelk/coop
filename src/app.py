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
temperature = None
humidity = None
door_state = None
lock = Lock()

# Background thread for managing coop in real-time.
def background():
    import board
    from dht22 import DHT22
    from door import DOOR

    global temperature, humidity, door_state
    dht = DHT22(board.D21)
    door = DOOR()
    while True:
        temp, hum = dht.get_temperature_and_humidity()
        state = door.get_state()
        #print("Temperature={0:0.1f}F Humidity={1:0.1f}% Door={s}".format(temp, hum, door.get_state()))
        with lock:
            temperature = temp
            humidity = hum
            door_state = state
        time.sleep(2.0)

@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(target=update_data)

def update_data():
    while True:
        with lock:
            temp = temperature
            hum = humidity
            state = door_state
        to_send = {
          'temp': ("%0.1f" % temp) + u'\N{DEGREE SIGN}' + "F" if temp is not None else "",
          'hum': "%0.1f%%" % hum if hum is not None else "",
          'state': state if state is not None else "",
          'curtime': str(datetime.now())
        }
        socketio.emit('data', to_send)
        time.sleep(2.0)

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

    # Start the Flask app
    socketio.run(app, debug=False, host='0.0.0.0')
