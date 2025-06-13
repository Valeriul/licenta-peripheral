from module.module import Sensor
import json
import utils.battery as battery

class GasSensor(Sensor):
    def __init__(self, i2c_address):
        super().__init__(i2c_address)
        self.i2c = None  # Will be set by ModuleManager
        self.i2c_address = i2c_address  # Will be set by ModuleManager

    def get_state(self):
        """Read gas sensor value and return as JSON"""
        try:
            if self.i2c and self.i2c_address is not None:
                # Read data from the gas sensor
                gas_value, voltage = self.read_mq5_voltage()
                print(f"GasSensor: Read value {gas_value} (Voltage: {voltage:.2f}V) from I2C address {self.i2c_address}")
            else:
                print("⚠️ GasSensor: I2C not available, cannot read value")
                gas_value = 0
            
            return json.dumps({
                "gasValue": gas_value,
                "batteryLevel": battery.getBatteryPercentage()
            })
        except Exception as e:
            print(f"❌ GasSensor: Error reading state: {e}")
            return json.dumps({"error": str(e)})

    def read_mq5_voltage(self):
        control_byte = 0x40  # Canal 0, DAC off
        self.i2c.writeto(self.i2c_address, bytes([control_byte]))
        self.i2c.readfrom(self.i2c_address, 1)  # Ignorăm primul byte
        value = self.i2c.readfrom(self.i2c_address, 1)[0]
        voltage = (value / 255) * 3.3
        return value, voltage