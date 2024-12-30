from _thread import allocate_lock
import ports
import led
import os

def generate_uuid():
    # Generate a pseudo-random 16-character hexadecimal string
    return ''.join(f"{b:02x}" for b in os.urandom(8))

class ModuleManager:

    modules = {}
    _lock = allocate_lock()  # Lock for thread safety

    @staticmethod
    def create_module(module_type, port_number):
        with ModuleManager._lock:
            port = ports.available_ports.get(port_number)
            if(port.get_module() is None):
                if module_type == 'led':
                    module = led.Led(port)
                else:
                    raise ValueError('Invalid module type')
                uuid = generate_uuid()
                ModuleManager.modules[uuid] = module
                port.set_module(module)
        
    @staticmethod
    def remove_module(uuid):
        with ModuleManager._lock:
            module = ModuleManager.modules.pop(uuid, None)
            if module:
                available_ports[port.identification_pin].remove_module()
        
    @staticmethod
    def remove_module_by_port(identification_pin):
        with ModuleManager._lock:
            for uuid, module in ModuleManager.modules.items():
                if module.port.identification_pin == identification_pin and module:
                    module.__del__()
                    ModuleManager.modules.pop(uuid)
                    ports.available_ports[module.port.identification_pin].remove_module()
                    break
        
    @staticmethod
    def get_module(uuid):
        with ModuleManager._lock:
            return ModuleManager.modules.get(uuid)
