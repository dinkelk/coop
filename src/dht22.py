import adafruit_dht
import board
import time

class DHT22():
    def __init__(self, pin):
        self.dht = adafruit_dht.DHT22(pin)

    def get_temperature_and_humidity(self):
        temp_f = None
        temp_c = None
        hum = None

        # Try up to 3 times:
        for idx in range(3):
            try:
                temp_c = self.dht.temperature
                hum = self.dht.humidity
                break
            except (RuntimeError, OverflowError):
                time.sleep(2.5)
                continue

        if temp_c is not None:
            temp_f = temp_c * (9.0/5.0) + 32.0
        return temp_f, hum

if __name__ == '__main__':
    dht = DHT22(board.D21)
    while True:
        temp_f, hum = dht.get_temperature_and_humidity()
        print("Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp_f, hum))
        time.sleep(2.0)
