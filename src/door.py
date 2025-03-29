import RPi.GPIO as GPIO
GPIO.setwarnings(False)
import time

# in1 = 24
# in2 = 23
# o_pin = 17
# c_pin = 4

class SWITCH3():
    def __init__(self, o_pin, c_pin, open_callback=None, close_callback=None):
        # Set up callbacks:
        self.o_pin = o_pin
        self.c_pin = c_pin
        self.open_callback = open_callback
        self.close_callback = close_callback

        # Set up switch detection:
        GPIO.setup(self.o_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.c_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.o_pin, GPIO.BOTH, callback=self.switch_activated, bouncetime=600)
        GPIO.add_event_detect(self.c_pin, GPIO.BOTH, callback=self.switch_activated, bouncetime=600)

    # Open or close door if switch activated:
    def switch_activated(self, channel):
        # Wait just a bit for stability, so we make sure we get
        # a good reading right after the interrupt.
        time.sleep(0.15)
        o_read = GPIO.input(self.o_pin)
        c_read = GPIO.input(self.c_pin)
        if o_read != c_read:
            if o_read == GPIO.HIGH:
                # # TODO - configure SWITCH3 with open callback we call here instead
                # #print("Opening!")
                # self.override = True
                # self.open()
                if self.open_callback:
                    self.open_callback()
            elif c_read == GPIO.HIGH:
                # # TODO - configure SWITCH3 with close callback we call here instead
                # #print("Closing!")
                # self.override = True
                # self.close()
                if self.close_callback:
                    self.close_callback()

    # When called, stops door if switch is neutral.
    def is_switch_neutral(self):
        o_read = GPIO.input(self.o_pin)
        c_read = GPIO.input(self.c_pin)
        if o_read == c_read:
            return True
        else:
            return False
            # # TODO - configure SWITCH3 with nuetral callback we call here instead
            # #print("Do nothing.")
            # self.override = False
            # self.stop(state=nuetral_state)
            #if neutral_callback:
            #    neutral_callback()


class DOOR():
    def __init__(self, in1, in2):
        # Define state and pins used
        self.in1 = in1
        self.in2 = in2
        self.state = "stopped"

        # Set up motor controller:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.in1, GPIO.OUT)
        GPIO.setup(self.in2, GPIO.OUT)
        self.stop()

        # # Set up switch detection:
        # GPIO.setup(o_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # GPIO.setup(c_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # GPIO.add_event_detect(o_pin, GPIO.BOTH, callback=self.switch_activated, bouncetime=600)
        # GPIO.add_event_detect(c_pin, GPIO.BOTH, callback=self.switch_activated, bouncetime=600)

    # # Open or close door if switch activated:
    # def switch_activated(self, channel):
    #     # Wait just a bit for stability, so we make sure we get
    #     # a good reading right after the interrupt.
    #     time.sleep(0.15)
    #     o_read = GPIO.input(o_pin)
    #     c_read = GPIO.input(c_pin)
    #     if o_read != c_read:
    #         if o_read == GPIO.HIGH:
    #             #print("Opening!")
    #             self.override = True
    #             self.open()
    #         elif c_read == GPIO.HIGH:
    #             #print("Closing!")
    #             self.override = True
    #             self.close()

    # # When called, stops door if switch is neutral.
    # def check_if_switch_neutral(self, nuetral_state="stopped"):
    #     # Wait just a bit for stability:
    #     o_read = GPIO.input(o_pin)
    #     c_read = GPIO.input(c_pin)
    #     if o_read == c_read:
    #         #print("Do nothing.")
    #         self.override = False
    #         self.stop(state=nuetral_state)

    def get_state(self):
        return self.state

    # def get_override(self):
    #     return self.override

    def stop(self, state="stopped"):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        self.state = state

    def open(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        self.state = "opening"

    def close(self):
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        self.state = "closing"

    def open_then_stop(self):
        self.open()
        time.sleep(30)
        self.stop()
        self.state = "open"

    def close_then_stop(self):
        self.close()
        time.sleep(30)
        self.stop()
        self.state = "closed"

if __name__ == "__main__":
    door = DOOR()
    door.close_then_stop()
    door.open_then_stop()
