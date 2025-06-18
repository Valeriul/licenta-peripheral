class Module:
    def __init__(self, i2c_instance,i2c_address):
        self.state = None  # Initialize the state to None
        self.i2c_address = i2c_address   # Assign the I2C address
        self.i2c = None  # Will be set by ModuleManager

    def get_state(self):
        pass

    def set_i2c(self, i2c_instance):
        """Set the I2C instance for communication"""
        self.i2c = i2c_instance

class Sensor(Module):
    def __init__(self,i2c_instance, i2c_address):
        super().__init__(i2c_instance, i2c_address)  # Call the parent class initializer


class Control(Module):
    def __init__(self, i2c_instance, i2c_address):
        super().__init__(i2c_instance, i2c_address)  # Call the parent class initializer

    def set_state(self, state):
        pass
    
from module.controls.led import Led
from module.sensors.gas import GasSensor
from module.controls.relay import Relay
from module.sensors.temperature import TemperatureSensor
    
class ModuleFactory:
    @staticmethod
    def create_module(module_type,i2c_instance, i2c_address):
        if module_type.lower() == Led.__name__.lower():
            return Led(i2c_instance, i2c_address)
        elif module_type.lower() == GasSensor.__name__.lower():
            return GasSensor(i2c_instance, i2c_address)
        elif module_type.lower() == Relay.__name__.lower():
            return Relay(i2c_instance, i2c_address)
        elif module_type.lower() == TemperatureSensor.__name__.lower():
            return TemperatureSensor(i2c_instance, i2c_address)
        else:
            raise ValueError("Invalid module type")