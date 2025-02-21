from _thread import allocate_lock
import socket
import ports
import json
import os
import wifi_connect
from module import Control,ModuleFactory

def generate_uuid():
    # Generate a pseudo-random 16-character hexadecimal string
    return ''.join(f"{b:02x}" for b in os.urandom(8))

class ModuleManager:

    modules = {}
    _lock = allocate_lock()  # Lock for thread safety
    data_file = "modules.json"  # File to save module information
    port_history_file = "port_history.json"  # File to save port history

    with open("wifi_credentials.json", "r") as f:
        central_ip = json.load(f).get("central_ip")
        
    @staticmethod
    async def save_modules():
        try:
            module_list = []
            for uuid, module in ModuleManager.modules.items():
                print(f"Saving module: UUID={uuid}, Type={type(module).__name__}, Port={module.port.identification_pin}")  # Debug
                module_list.append({
                    "uuid": uuid,
                    "module_type": type(module).__name__,
                    "port_number": module.port.identification_pin
                })
            
            # Write the entire list as a JSON array
            with open(ModuleManager.data_file, "w") as f:
                json.dump(module_list, f)
            await ModuleManager.refresh_modules_of_server(ModuleManager.central_ip, 5002, "/rasberry/Peripheral/refreshPeripherals", ModuleManager.modules)
        except Exception as e:
            print(f"Error saving modules: {e}")


    @staticmethod
    async def load_modules():
        """Load modules from a JSON file."""
        with ModuleManager._lock:
            try:
                with open(ModuleManager.data_file, "r") as f:
                    json_data = json.load(f)
                    for module_info in json_data:
                        uuid = module_info["uuid"]
                        module_type = module_info["module_type"]
                        port_number = module_info["port_number"]

                        port = ports.available_ports.get(port_number)
                        if port is None:
                            print(f"Error: Port {port_number} not found.")
                            continue
                        
                        module = ModuleFactory.create_module(module_type, port)

                        ModuleManager.modules[uuid] = module
                        port.set_module(module)
                        print(f"Loaded module: UUID={uuid}, Type={module_type}, Port={port_number}")
                        await ModuleManager.refresh_modules_of_server(ModuleManager.central_ip, 5002, "/rasberry/Peripheral/refreshPeripherals", ModuleManager.modules)
            except Exception as e:
                print(f"Error loading modules: {e}")
 
                
    @staticmethod
    async def refresh_modules_of_server(host, port, endpoint, data):
        """Sends an HTTP POST request using MicroPython's socket module."""
        try:
            # Convert data to JSON string
            ip_address = wifi_connect.get_ip_address() + ":8080"
            json_data = [
                {
                    "PeripheralType": type(module).__name__,
                    "Uuid": uuid,
                    "Url": ip_address
                }
                for uuid, module in data.items()
            ]

            print(f"Sending POST request to {host}:{port}{endpoint} with data: {json_data}")  # Debug

            json_data = json.dumps(json_data)

            
            # Create a socket connection
            addr = socket.getaddrinfo(host, port)[0][-1]
            s = socket.socket()
            s.connect(addr)

            # Prepare HTTP headers and body
            request = (
                f"POST {endpoint} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                "Accept: */*\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(json_data)}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{json_data}"
            )

            # Send request
            s.send(request.encode())

            # Read the response
            response = s.recv(1024).decode()

            # Close the socket
            s.close()

        except Exception as e:
            print(f"❌ POST request failed: {e}")


    @staticmethod
    async def create_module(module_type, port_number):
        """Create a new module of the specified type on the given port."""
        with ModuleManager._lock:
            port = ports.available_ports.get(port_number)
            if port is None:
                print(f"Error: Port {port_number} not found.")
                return
            if port.get_module() is None:
                module = ModuleFactory.create_module(module_type, port)
                
                uuid = ModuleManager.get_uuid(type(module).__name__)
                ModuleManager.modules[uuid] = module
                port.set_module(module)
                await ModuleManager.save_modules()
                
    @staticmethod
    def save_entry_to_history(module_type, uuid):
        try:
            with open(ModuleManager.port_history_file, "r") as f:
                history = json.load(f)
        except Exception as e:
            history = {}
        
        if history.get(module_type) is None:
            history[module_type] = uuid
        
        try:
            with open(ModuleManager.port_history_file, "w") as f:
                json.dump(history, f)
        except Exception as e:
            print(f"Error saving entry to history: {e}")

    @staticmethod
    def get_uuid(module_type):
        try:
            with open(ModuleManager.port_history_file, "r") as f:
                history = json.load(f)
        except Exception as e:
            history = {}

        if history.get(module_type) is not None:
            return history.get(module_type)
            
        uuid = generate_uuid()
        ModuleManager.save_entry_to_history(module_type, uuid)
        return uuid
        
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
    async def remove_module_by_port(identification_pin):
        """Remove a module assigned to a specific port."""
        with ModuleManager._lock:
            for uuid, module in list(ModuleManager.modules.items()):
                if module.port.identification_pin == identification_pin:
                    ModuleManager.modules.pop(uuid)
                    ports.available_ports[module.port.identification_pin].remove_module()
                    module.__del__()
                    await ModuleManager.save_modules()
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
