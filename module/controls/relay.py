from module.module import Control
import json
import utils.battery as battery

class Relay(Control):
    def __init__(self,i2c_instance,i2c_address):  # ← Accepts i2c_address
        super().__init__(i2c_instance,i2c_address)  # ← Passes i2c_address to parent
        self.i2c = i2c_instance
        self.i2c_address = i2c_address
        self.set_state(0)

    def set_state(self, state):
        if state == 'HIGH' or state == 1:
            relay_value = 255
            self.state = 1
        elif state == 'LOW' or state == 0:
            relay_value = 0
            self.state = 0
        try:
            
            if self.i2c and self.i2c_address is not None:
                data = bytes([0x50, relay_value])
                self.i2c.writeto(self.i2c_address, data)                
            else:
                print("⚠️ RELAY: I2C not available, cannot set state")    
        except Exception as e:
            print(f"❌ RELAY: Error setting state: {e}")
            
    def set_i2c(self, i2c_instance):
        """Set the I2C instance for communication"""
        self.i2c = i2c_instance

    def get_state(self):
        return json.dumps({
            "isOn": bool(self.state),
            "batteryLevel": battery.getBatteryPercentage()
        })
    
    def __del__(self):
        self.set_state(0)