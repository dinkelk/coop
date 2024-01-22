import adafruit_dht
import board
import time

class DHT():
    def __init__(self):
        self.dht1 = adafruit_dht.DHT22(board.D21)

    def get_temp(self):
        print(str(self.dht1.temperature))
        return 19.9

    def get_temperature_and_humidity(self):
        temp_f = None
        temp_c = None
        hum = None
    
        # Try up to 3 times:
        for idx in range(3):
            try:
                temp_c = self.dht1.temperature
                hum = self.dht1.humidity 
                break
            except RuntimeError as e:
                time.sleep(2.0)
                continue
    
        if temp_c is not None:
            temp_f = temp_c * (9.0/5.0) + 32.0
        return temp_f, hum

#if __name__ == '__main__':
#    while True:
#        temp_f, hum = get_temperature_and_humidity()
#        print("Temperature={0:0.1f}F Humidity={1:0.1f}%".format(temp_f, hum))
#        time.sleep(2.0)
