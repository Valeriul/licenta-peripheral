from module.module import Control
import json
import utils.battery as battery

class Led(Control):
    def __init__(self, i2c_address):  # ← Accepts i2c_address
        super().__init__(i2c_address)  # ← Passes i2c_address to parent
        self.set_state(0)
        self.i2c = None  # Will be set by ModuleManager
        self.i2c_address = i2c_address  # Will be set by ModuleManager


    def set_state(self, state):
        """Set LED brightness by sending 8-bit PWM value over I2C"""
        print(f"🔅 LED: Setting brightness to {state}%")
        try:
            # Convert percentage to 0-100 range and validate
            state = max(0, min(100, float(state)))
            self.state = state
            
            # Convert percentage (0-100) to 8-bit value (0-255)
            pwm_value = int((state / 100.0) * 255)
            
            if self.i2c and self.i2c_address is not None:
                # Send command: [CMD_SET_PWM, pwm_value]
                data = bytes([0x40, pwm_value])
                self.i2c.writeto(self.i2c_address, data)                
            else:
                print("⚠️ LED: I2C not available, cannot set brightness")    
        except Exception as e:
            print(f"❌ LED: Error setting brightness: {e}")
            
    def set_i2c(self, i2c_instance):
        """Set the I2C instance for communication"""
        self.i2c = i2c_instance

    def get_state(self):
        return json.dumps({
            "brightness": self.state,
            "batteryLevel": battery.getBatteryPercentage()
        })
    
    def __del__(self):
        self.set_state(0)