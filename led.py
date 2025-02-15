from module import Control
from ports import Port
from machine import Pin, PWM
import json
import battery

class Led(Control):
    def __init__(self, port):
        self.port = port
        self.state = 0  # Initial LED state (0% brightness)

        self.PIN1 = PWM(Pin(self.port.working_pins[0], Pin.OUT))
        self.PIN1.freq(1000) 
        
        self.set_state(self.state)

    def set_state(self, state):
        state = float(state)

        self.state = state

        percent = state / 100
        duty_cycle = int(percent * 65535)
        self.PIN1.duty_u16(duty_cycle)


    def get_state(self):
        return json.dumps({
            "brightness": self.state,
            "batteryLevel": battery.getBatteryPercentage()
        })
    
    def __del__(self):
        self.set_state(0)
