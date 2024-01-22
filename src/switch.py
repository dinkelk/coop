import RPi.GPIO as GPIO
GPIO.setwarnings(False)                                                                                                                                                                                                                                                                     
import time
import door

o_pin = 4
c_pin = 17

GPIO.setmode(GPIO.BCM) 
GPIO.setup(o_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(c_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def switch_activated(channel):
    o_read = GPIO.input(o_pin)
    c_read = GPIO.input(c_pin)
    if o_read == c_read:
        print("Do nothing.")
        door.stop()
    elif o_read == GPIO.HIGH:
        print("Opening!")
        door.open()
    elif c_read == GPIO.HIGH:
        print("Closing!")
        door.close()
    else:
        door.stop()
        assert False
    
    if False:
        print("Switch activated! open: " + str(o_read) + " close: " + str(c_read))
    
GPIO.add_event_detect(o_pin, GPIO.BOTH, callback=switch_activated, bouncetime=500)
GPIO.add_event_detect(c_pin, GPIO.BOTH, callback=switch_activated, bouncetime=500)

if __name__ == "__main__":
    while(True):
        pass






















