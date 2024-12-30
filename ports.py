class Port:
    def __init__(self, identification_pin, working_pins):
        self._identification_pin = identification_pin  # Initialize with parameter
        self._working_pins = working_pins             # Initialize with parameter
        self._module = None                           # Initialize as None
    
    def set_module(self, module):
        self._module = module  # Set the module
    
    def get_module(self):
        return self._module    # Return the module
        
    def remove_module(self):
        self._module = None    # Remove the module

    @property
    def identification_pin(self):
        return self._identification_pin

    @property
    def working_pins(self):
        return self._working_pins


# Global map to store port values
available_ports = {
    28: Port(28, [0,1,2]),
    27: Port(27, [3,4,5]),
    26: Port(26, [6,7,8])
}
