from _thread import allocate_lock
import ports
import led
import os
from module import Control

def generate_uuid():
    # Generate a pseudo-random 16-character hexadecimal string
    return ''.join(f"{b:02x}" for b in os.urandom(8))

class ModuleManager:

    modules = {}
    _lock = allocate_lock()  # Lock for thread safety
    data_file = "modules.txt"  # File to save module information

    @staticmethod
    def save_modules():
        try:
            # Open the file and write data
            with open(ModuleManager.data_file, "w") as f:
                for uuid, module in ModuleManager.modules.items():
                    print(f"Saving module: UUID={uuid}, Type={type(module).__name__}, Port={module.port.identification_pin}")  # Debug
                    line = f"{uuid},{type(module).__name__},{module.port.identification_pin}\n"
                    f.write(line)
        except Exception as e:
            print(f"Error saving modules: {e}")


    @staticmethod
    def load_modules():
        """Load modules from a plain text file."""
        with ModuleManager._lock:
            try:
                with open(ModuleManager.data_file, "r") as f:
                    for line in f:
                        uuid, module_type, port_number = line.strip().split(",")
                        port = ports.available_ports.get(int(port_number))
                        if port:
                            if module_type.lower() == "led":
                                module = led.Led(port)
                            else:
                                print(f"Unknown module type: {module_type}")
                                continue
                            ModuleManager.modules[uuid] = module
                            port.set_module(module)
            except Exception as e:
                print(f"Error loading modules: {e}")

    @staticmethod
    def create_module(module_type, port_number):
        """Create a new module of the specified type on the given port."""
        with ModuleManager._lock:
            port = ports.available_ports.get(port_number)
            if port is None:
                print(f"Error: Port {port_number} not found.")
                return
            if port.get_module() is None:
                if module_type.lower() == "led":
                    module = led.Led(port)
                else:
                    raise ValueError("Invalid module type")
                uuid = generate_uuid()
                ModuleManager.modules[uuid] = module
                port.set_module(module)
                ModuleManager.save_modules()

    @staticmethod
    def remove_module(uuid):
        """Remove a module by its UUID."""
        with ModuleManager._lock:
            module = ModuleManager.modules.pop(uuid, None)
            if module:
                ports.available_ports[module.port.identification_pin].remove_module()
                module.__del__()
                ModuleManager.save_modules()
                
    @staticmethod
    def remove_module_by_port(identification_pin):
        """Remove a module assigned to a specific port."""
        with ModuleManager._lock:
            for uuid, module in list(ModuleManager.modules.items()):
                if module.port.identification_pin == identification_pin:
                    ModuleManager.modules.pop(uuid)
                    ports.available_ports[module.port.identification_pin].remove_module()
                    module.__del__()
                    ModuleManager.save_modules()
                    break


    @staticmethod
    def get_module(uuid):
        """Retrieve a module by its UUID."""
        with ModuleManager._lock:
            return ModuleManager.modules.get(uuid)
        
    @staticmethod
    def get_modules():
        """Retrieve all modules."""
        with ModuleManager._lock:
            return ModuleManager.modules.copy()

    @staticmethod
    def get_module_state(uuid):
        """Retrieve the state of a module by UUID."""
        with ModuleManager._lock:
            module = ModuleManager.modules.get(uuid)
            if module:
                return module.get_state()
            return {"error": "Module not found"}

    @staticmethod
    def set_module_state(uuid, state):
        """Set the state of a module by UUID."""
        with ModuleManager._lock:
            module = ModuleManager.modules.get(uuid)
            if module and isinstance(module, Control):
                module.set_state(state)
                return {"new_state": state}
            return {"error": "Invalid module or module does not support state changes"}
