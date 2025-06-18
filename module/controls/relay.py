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
        """Set relay state by sending high/low command over I2C"""
        # Convert to boolean and set full 8 bits (255) for high, 0 for low
        relay_value = 255 if state else 0
        state_text = "HIGH" if state else "LOW"
        
        print(f"🔌 RELAY: Setting state to {state_text} (0x{relay_value:02X})")
        try:
            self.state = 1 if state else 0
            
            if self.i2c and self.i2c_address is not None:
                # Send command: [CMD_SET_RELAY, relay_value] where relay_value is 255 or 0
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