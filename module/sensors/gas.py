from module.module import Sensor
import json
import utils.battery as battery
import math

class GasSensor(Sensor):
    def __init__(self, i2c_instance, i2c_address):
        super().__init__(i2c_instance, i2c_address)
        self.i2c = i2c_instance
        self.i2c_address = i2c_address
        
        # MQ-5 sensor parameters for butane (lighter gas) detection
        self.RL = 10.0  # Load resistance in kOhms
        self.Ro = 6.5   # Pre-calibrated resistance for butane in clean air
        self.a = 3616.1 # Curve fitting parameter a for butane
        self.b = -2.675 # Curve fitting parameter b for butane

    def get_state(self):
        """Read gas sensor value and return butane PPM as JSON"""
        try:
            if self.i2c and self.i2c_address is not None:
                # Read data from the gas sensor and convert to PPM
                ppm_value, voltage = self.read_butane_ppm()
                print(f"GasSensor: Read {ppm_value:.2f} PPM butane (Voltage: {voltage:.2f}V) from I2C address {self.i2c_address}")
            else:
                print("⚠️ GasSensor: I2C not available, cannot read value")
                ppm_value = 0
            
            return json.dumps({
                "gasValue": round(ppm_value, 2),
                "batteryLevel": battery.getBatteryPercentage()
            })
        except Exception as e:
            print(f"❌ GasSensor: Error reading state: {e}")
            return json.dumps({"error": str(e)})

    def read_butane_ppm(self):
        """Read MQ-5 sensor and convert to butane PPM"""
        try:
            # Read raw ADC value
            control_byte = 0x40  # Canal 0, DAC off
            self.i2c.writeto(self.i2c_address, bytes([control_byte]))
            self.i2c.readfrom(self.i2c_address, 1)  # Ignore first byte
            adc_value = self.i2c.readfrom(self.i2c_address, 1)[0]
            
            # Convert ADC to voltage (0-3.3V range)
            voltage = (adc_value / 255.0) * 3.3
            
            # Prevent division by zero
            if voltage <= 0.1:  # Minimum threshold
                return 0, voltage
            
            # Convert voltage to sensor resistance
            # Rs = ((Vc * RL) / Vout) - RL
            Rs = ((3.3 * self.RL) / voltage) - self.RL
            
            # Ensure Rs is positive
            if Rs <= 0:
                return 0, voltage
            
            # Calculate Rs/Ro ratio
            ratio = Rs / self.Ro
            
            # Convert to PPM using logarithmic equation for butane
            # PPM = a * (Rs/Ro)^b
            if ratio > 0:
                ppm = self.a * math.pow(ratio, self.b)
            else:
                ppm = 0
            
            # Ensure PPM is within reasonable bounds for lighter gas
            ppm = max(0, min(ppm, 5000))  # Cap between 0-5000 PPM for butane
            
            return ppm, voltage
            
        except Exception as e:
            print(f"❌ GasSensor: Error calculating butane PPM: {e}")
            return 0, 0