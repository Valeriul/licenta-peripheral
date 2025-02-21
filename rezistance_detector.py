import machine
import time
from module_manager import ModuleManager
import uasyncio

# Define the ADC pins
adc_pins = {
    28: machine.ADC(28),
    27: machine.ADC(27),
    26: machine.ADC(26)
}

available_modules = {
    'led': [100000,0.3],
}


# Reference voltage of the Raspberry Pi Pico
VREF = 3.3

refference_resistor = 10000

# Global map to store pin values
pin_values = {}

# Function to update pin values continuously
async def read_pins():
    global pin_values
    while True:
        for pin, adc in adc_pins.items():
            raw_value = adc.read_u16()
            voltage = (raw_value / 65535) * VREF
            if voltage < 0.1:
                await ModuleManager.remove_module_by_port(pin)
            else:
                rezistance = round(((VREF * refference_resistor) / voltage) - refference_resistor, 2)
                for module_type, values in available_modules.items():
                    if values[0] * (1 - values[1]) <= rezistance <= values[0] * (1 + values[1]):
                        await ModuleManager.create_module(module_type, pin)
                        break
        await uasyncio.sleep(0.5)  # ✅ Use async sleep instead of time.sleep()
