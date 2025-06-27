from module.module import Sensor
import json
import utils.battery as battery

class TemperatureSensor(Sensor):
    def __init__(self,i2c_instance,i2c_address):
        super().__init__(i2c_instance,i2c_address)
        self.i2c = i2c_instance
        self.i2c_address = i2c_address

    def get_state(self):
        try:
            if self.i2c and self.i2c_address is not None:
                # Read data from the LM75B temperature sensor
                temperature_c = self.read_lm75b_temperature()
                temperature_f = (temperature_c * 9/5) + 32
                print(f"🌡️ TemperatureSensor: Read {temperature_c:.2f}°C ({temperature_f:.2f}°F) from I2C address 0x{self.i2c_address:02X}")
            else:
                print("⚠️ TemperatureSensor: I2C not available, cannot read value")
                temperature_c = 0
                temperature_f = 32
            
            return json.dumps({
                "temperatureC": round(temperature_c, 2),
                "batteryLevel": battery.getBatteryPercentage()
            })
        except Exception as e:
            print(f"❌ TemperatureSensor: Error reading state: {e}")
            return json.dumps({"error": str(e)})

    def read_lm75b_temperature(self):
        """Read temperature from LM75B sensor"""

        TEMP_REGISTER = 0x00
        
        self.i2c.writeto(self.i2c_address, bytes([TEMP_REGISTER]))
        data = self.i2c.readfrom(self.i2c_address, 2)
        
        raw_temp = (data[0] << 8) | data[1]
        temp_raw = raw_temp >> 5
        
        if temp_raw & 0x400:
            temp_raw -= 0x800 
        
        temperature = temp_raw * 0.125
        
        return temperature