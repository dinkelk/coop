import adafruit_dht
import RPi.GPIO as GPIO
import board
import time

class DHT22():
    # Provide data pin and power pin. We power via GPIO so that we can cycle power
    # between each read of the sensor. This works around the lock ups that frequently
    # occur with these cheap sensors.
    def __init__(self, data_pin, power_pin):
        self.pwr = int(power_pin)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pwr, GPIO.OUT)
        GPIO.output(self.pwr, GPIO.LOW)
        self.dht = adafruit_dht.DHT22(data_pin)

    def get_temperature_and_humidity(self):
        temp_f = None
        temp_c = None
        hum = None

        # Turn on power to sensor:
        GPIO.output(self.pwr, GPIO.HIGH)
        time.sleep(2.2)

        # Try up to 3 times:
        for idx in range(3):
            try:
                temp_c = self.dht.temperature
                hum = self.dht.humidity
                break
            except (RuntimeError, OverflowError):
                time.sleep(2.2)
                continue

        # Turn off power to sensor:
        GPIO.output(self.pwr, GPIO.LOW)

        if temp_c is not None:
            temp_f = temp_c * (9.0/5.0) + 32.0
        return temp_f, hum

if __name__ == '__main__':
    dht = DHT22(board.D21)
    while True:
        temp_f, hum = dht.get_temperature_and_humidity()
        print("Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp_f, hum))
        time.sleep(2.0)
