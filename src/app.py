from flask import Flask, render_template
from threading import Thread, Lock
import dht22
import time
import subprocess

app = Flask(__name__, template_folder="../templates")

def get_linux_uptime():
    output = subprocess.check_output('uptime -s', shell=True)
    uptime = output.decode().strip()
    return uptime

# Global variables to store data for page:
temperature = None
humidity = None
lock = Lock()

# Background thread for managing coop in real-time.
def background():
    global temperature, humidity
    dht = dht22.DHT()
    while True:
        temp, hum = dht.get_temperature_and_humidity()
        print("Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp, hum))
        with lock:
            temperature = temp
            humidity = hum
        time.sleep(2.0)

# Route for the home page
@app.route('/')
def index():
    # Read temperature and humidity from sensor
    with lock:
        temp = temperature
        hum = humidity

    from datetime import datetime

    current_time = datetime.now()

    # Render the template with temperature and humidity values
    return render_template(
        'index.html', 
        temperature=("{0:0.1f}".format(temp) if temp is not None else None),
        humidity=("{0:0.1f}".format(hum) if hum is not None else None),
        uptime=get_linux_uptime(),
        curtime=current_time
    )

# Route for controlling the linear actuator
@app.route('/actuator/<action>')
def actuator(action):
    # Code to control the linear actuator based on the action parameter
    # For example, you can use GPIO libraries to control the actuator

    # Return a response indicating the action performed
    return f'Actuator {action}'

if __name__ == '__main__':
    # Start the background thread
    thread = Thread(target=background)
    thread.daemon = True
    thread.start()

    # Start the Flask app
    app.run(debug=False, host='0.0.0.0')
