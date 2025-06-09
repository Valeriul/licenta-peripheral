from module.module import Control
import json
import utils.battery as battery

class Led(Control):
    def __init__(self):
        super().__init__()
        self.state = 0  # Initial LED state (0% brightness)
        self.i2c = None  # Will be set by ModuleManager
        self.i2c_address = None  # Will be set by ModuleManager
        
        # I2C command constants
        self.CMD_SET_PWM = 0x01  # Command to set PWM duty cycle

    def set_state(self, state):
        """Set LED brightness by sending 8-bit PWM value over I2C"""
        try:
            # Convert percentage to 0-100 range and validate
            state = max(0, min(100, float(state)))
            self.state = state
            
            # Convert percentage (0-100) to 8-bit value (0-255)
            pwm_value = int((state / 100.0) * 255)
            
            if self.i2c and self.i2c_address is not None:
                # Send command: [CMD_SET_PWM, pwm_value]
                data = bytes([self.CMD_SET_PWM, pwm_value])
                self.i2c.writeto(self.i2c_address, data)
                print(f"🔅 LED: Set brightness to {state}% (PWM: {pwm_value}/255) at I2C 0x{self.i2c_address:02x}")
            else:
                print("⚠️ LED: I2C not available, cannot set brightness")
                
        except Exception as e:
            print(f"❌ LED: Error setting brightness: {e}")

    def get_state(self):
        return json.dumps({
            "brightness": self.state,
            "batteryLevel": battery.getBatteryPercentage()
        })
    
    def __del__(self):
        self.set_state(0)