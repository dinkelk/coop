import RPi.GPIO as GPIO
GPIO.setwarnings(False)                                                                                                                                                                                                                                                                     
import time

in1 = 24
in2 = 23
ena = 25

def stop():
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(ena, GPIO.LOW)
  
def open():
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    GPIO.output(ena, GPIO.HIGH)
  
def close():
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(ena, GPIO.HIGH)

def open_door():
    open()
    time.sleep(30)
    stop()

def close_door():
    close()
    time.sleep(30)
    stop()

GPIO.setmode(GPIO.BCM) 
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(ena, GPIO.OUT)
stop()

if __name__ == "__main__":
    open_door()
    close_door()





