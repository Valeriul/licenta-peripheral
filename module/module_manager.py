from _thread import allocate_lock
import socket
import json
import os
import uasyncio as asyncio
from machine import I2C, Pin
import wifi.wifi_connect as wifi_connect
from module.module import Control, ModuleFactory

def generate_uuid():
    # Generate a pseudo-random 16-character hexadecimal string
    return ''.join(f"{b:02x}" for b in os.urandom(8))

class ModuleManager:

    modules = {}
    _lock = allocate_lock()  # Lock for thread safety
    data_file = "modules.json"  # File to save module information
    i2c_history_file = "i2c_history.json"  # File to save I2C history
    
    # Dictionary to map I2C addresses to module types
    i2c_module_mapping = {
        0x49: "Led",
        0x48: "GasSensor",
    }
    
    # I2C detection attributes
    i2c = None
    known_i2c_devices = set()
    scan_interval = 1.0  # Scan every 1 second
    i2c_initialized = False

    @staticmethod
    def initialize_i2c(scl_pin=5, sda_pin=4, freq=100000):
        """Initialize I2C interface for device detection"""
        try:
            ModuleManager.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=freq)
            ModuleManager.i2c_initialized = True
            print(f"I2C initialized: SCL={scl_pin}, SDA={sda_pin}, Freq={freq}Hz")
        except Exception as e:
            print(f"Failed to initialize I2C: {e}")
            ModuleManager.i2c_initialized = False

    @staticmethod
    async def detect_i2c_modules():
        """Continuously scan for I2C devices and manage modules"""
        if not ModuleManager.i2c_initialized:
            ModuleManager.initialize_i2c()
        
        if not ModuleManager.i2c_initialized:
            print("❌ I2C not initialized, cannot detect modules")
            return
            
        print("🚀 Starting I2C module detection...")
        
        while True:
            try:
                # Scan I2C bus
                current_devices = set(ModuleManager.i2c.scan())
                
                # Handle newly connected devices
                new_devices = current_devices - ModuleManager.known_i2c_devices
                if new_devices:
                    for address in new_devices:
                        print(f"🔌 New I2C device detected at address 0x{address:02x}")
                        await ModuleManager._handle_new_i2c_device(address)
                
                # Handle disconnected devices
                removed_devices = ModuleManager.known_i2c_devices - current_devices
                if removed_devices:
                    for address in removed_devices:
                        print(f"🔌 I2C device disconnected at address 0x{address:02x}")
                        await ModuleManager._handle_removed_i2c_device(address)
                
                # Update known devices
                ModuleManager.known_i2c_devices = current_devices
                
                # Debug info (only print if devices changed)
                if new_devices or removed_devices:
                    if current_devices:
                        addresses = [f"0x{addr:02x}" for addr in sorted(current_devices)]
                        print(f"📡 Active I2C devices: {', '.join(addresses)}")
                    else:
                        print("📡 No I2C devices detected")
                        
            except Exception as e:
                print(f"❌ Error during I2C scan: {e}")
            
            # Wait before next scan
            await asyncio.sleep(ModuleManager.scan_interval)

    @staticmethod
    async def _handle_new_i2c_device(i2c_address):
        """Handle a newly detected I2C device"""
        try:
            # Check if we have a mapping for this I2C address
            module_type = ModuleManager.i2c_module_mapping.get(i2c_address)
            
            if module_type:
                print(f"✅ Creating {module_type} module for I2C address 0x{i2c_address:02x}")
                await ModuleManager.create_module_by_i2c_address(i2c_address)
            else:
                print(f"⚠️  Unknown I2C device at 0x{i2c_address:02x} - no module mapping found")
                await ModuleManager._try_identify_i2c_device(i2c_address)
                
        except Exception as e:
            print(f"❌ Error handling new I2C device 0x{i2c_address:02x}: {e}")

    @staticmethod
    async def _handle_removed_i2c_device(i2c_address):
        """Handle a disconnected I2C device"""
        try:
            print(f"🗑️  Removing module for I2C address 0x{i2c_address:02x}")
            await ModuleManager.remove_module_by_i2c_address(i2c_address)
        except Exception as e:
            print(f"❌ Error removing I2C device 0x{i2c_address:02x}: {e}")

    @staticmethod
    async def _try_identify_i2c_device(i2c_address):
        """Attempt to identify unknown I2C device"""
        try:
            # Try to read a few bytes to see if device responds
            test_data = ModuleManager.i2c.readfrom(i2c_address, 1)
            print(f"🔍 Device 0x{i2c_address:02x} responded with: {test_data.hex()}")
            
            # Check common device patterns
            await ModuleManager._check_common_device_patterns(i2c_address)
            
        except Exception as e:
            print(f"🔍 Device 0x{i2c_address:02x} identification failed: {e}")

    @staticmethod
    async def _check_common_device_patterns(i2c_address):
        """Check for common I2C device patterns to auto-identify"""
        try:
            # Common device ID registers to check
            id_registers = [0x00, 0x0F, 0xFC, 0xFD, 0xFE, 0xFF]
            
            for reg in id_registers:
                try:
                    # Write register address and read response
                    ModuleManager.i2c.writeto(i2c_address, bytes([reg]))
                    response = ModuleManager.i2c.readfrom(i2c_address, 1)
                    print(f"🔍 Device 0x{i2c_address:02x} register 0x{reg:02x}: 0x{response[0]:02x}")
                    
                    # Add device identification logic here
                    if i2c_address == 0x48 and reg == 0x00:
                        print(f"🎯 Possibly a temperature sensor (common at 0x48)")
                    elif i2c_address in [0x20, 0x21, 0x22, 0x23] and reg == 0x00:
                        print(f"🎯 Possibly an I/O expander or LED controller")
                        
                except:
                    continue  # Register not readable, try next
                    
        except Exception as e:
            print(f"🔍 Pattern check failed for 0x{i2c_address:02x}: {e}")

    @staticmethod
    def set_i2c_scan_interval(interval):
        """Set the I2C scan interval in seconds"""
        ModuleManager.scan_interval = max(0.1, interval)  # Minimum 100ms
        print(f"📡 I2C scan interval set to {ModuleManager.scan_interval}s")

    @staticmethod
    def get_current_i2c_devices():
        """Get currently detected I2C devices"""
        return ModuleManager.known_i2c_devices.copy()

    @staticmethod
    def manual_i2c_scan():
        """Perform a one-time manual I2C scan"""
        if not ModuleManager.i2c_initialized:
            ModuleManager.initialize_i2c()
        
        if not ModuleManager.i2c_initialized:
            print("❌ I2C not initialized")
            return []
            
        try:
            devices = ModuleManager.i2c.scan()
            print(f"📡 Manual scan found {len(devices)} devices:")
            for addr in sorted(devices):
                print(f"  - 0x{addr:02x}")
            return devices
        except Exception as e:
            print(f"❌ Manual scan failed: {e}")
            return []
        
    @staticmethod
    async def save_modules():
        try:
            module_list = []
            for uuid, module in ModuleManager.modules.items():
                print(f"Saving module: UUID={uuid}, Type={type(module).__name__}, I2C=0x{module.i2c_address:02x}")  # Debug
                module_list.append({
                    "uuid": uuid,
                    "module_type": type(module).__name__,
                    "i2c_address": module.i2c_address
                })
            
            # Write the entire list as a JSON array
            with open(ModuleManager.data_file, "w") as f:
                json.dump(module_list, f)
            central_ip = ModuleManager.get_central_ip()
            await ModuleManager.refresh_modules_of_server(central_ip, 5002, "/rasberry/Peripheral/refreshPeripherals", ModuleManager.modules)
        except Exception as e:
            print(f"Error saving modules: {e}")
            
    @staticmethod
    def get_central_ip():
        with open("wifi_credentials.json", "r") as f:
            return json.load(f).get("central_ip")

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
                        i2c_address = module_info["i2c_address"]

                        try:
                            module = ModuleFactory.create_module(module_type, i2c_address)
                            module.set_i2c(ModuleManager.i2c)  # ← Add this line
                            
                            ModuleManager.modules[uuid] = module
                            print(f"Loaded module: UUID={uuid}, Type={module_type}, I2C=0x{i2c_address:02x}")
                                                
                        except Exception as e:
                            print(f"Error creating module {module_type} at I2C 0x{i2c_address:02x}: {e}")
                            continue
                        
                central_ip = ModuleManager.get_central_ip()
                await ModuleManager.refresh_modules_of_server(central_ip, 5002, "/rasberry/Peripheral/refreshPeripherals", ModuleManager.modules)
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
    async def create_module_by_i2c_address(i2c_address):
        """Create a new module based on detected I2C address."""
        with ModuleManager._lock:
            # Check if module already exists for this I2C address
            for module in ModuleManager.modules.values():
                if hasattr(module, 'i2c_address') and module.i2c_address == i2c_address:
                    print(f"Module already exists for I2C address 0x{i2c_address:02x}")
                    return
            
            # Get module type from mapping
            module_type = ModuleManager.i2c_module_mapping.get(i2c_address)
            if module_type is None:
                print(f"No module type mapped for I2C address 0x{i2c_address:02x}")
                return
                
            try:
                module = ModuleFactory.create_module(module_type, i2c_address)
                module.set_i2c(ModuleManager.i2c)  # ← Add this line
                
                uuid = ModuleManager.get_uuid(type(module).__name__)
                ModuleManager.modules[uuid] = module
                
                print(f"Created module: {module_type} at I2C address 0x{i2c_address:02x}")
                await ModuleManager.save_modules()
                
            except Exception as e:
                print(f"Error creating module for I2C address 0x{i2c_address:02x}: {e}")

    @staticmethod
    async def create_module(module_type):
        """Create a new module of the specified type (for manual creation)."""
        with ModuleManager._lock:
            try:
                module = ModuleFactory.create_module(module_type)
                uuid = ModuleManager.get_uuid(type(module).__name__)
                ModuleManager.modules[uuid] = module
                await ModuleManager.save_modules()
                return module
            except Exception as e:
                print(f"Error creating module {module_type}: {e}")
                return None
                
    @staticmethod
    def save_entry_to_history(module_type, uuid):
        try:
            with open(ModuleManager.i2c_history_file, "r") as f:
                history = json.load(f)
        except Exception as e:
            history = {}
        
        if history and history.get(module_type) is None:
            history[module_type] = uuid
        
        try:
            with open(ModuleManager.i2c_history_file, "w") as f:
                json.dump(history, f)
        except Exception as e:
            print(f"Error saving entry to history: {e}")

    @staticmethod
    def get_uuid(module_type):
        try:
            with open(ModuleManager.i2c_history_file, "r") as f:
                history = json.load(f)
        except Exception as e:
            history = {}
        
        if isinstance(history, dict) and history and history.get(module_type) is not None:
            return history.get(module_type)
            
        uuid = generate_uuid()
        ModuleManager.save_entry_to_history(module_type, uuid)
        return uuid
        
    @staticmethod
    async def remove_module(uuid):
        """Remove a module by its UUID."""
        with ModuleManager._lock:
            module = ModuleManager.modules.pop(uuid, None)
            if module:
                try:
                    module.__del__()
                except:
                    pass
                await ModuleManager.save_modules()
                
    @staticmethod
    async def remove_module_by_i2c_address(i2c_address):
        """Remove a module assigned to a specific I2C address."""
        with ModuleManager._lock:
            for uuid, module in list(ModuleManager.modules.items()):
                if hasattr(module, 'i2c_address') and module.i2c_address == i2c_address:
                    ModuleManager.modules.pop(uuid)
                    try:
                        module.__del__()
                    except:
                        pass
                    print(f"Removed module at I2C address 0x{i2c_address:02x}")
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

    @staticmethod
    def add_i2c_mapping(i2c_address, module_type):
        """Add a new I2C address to module type mapping."""
        ModuleManager.i2c_module_mapping[i2c_address] = module_type
        print(f"Added I2C mapping: 0x{i2c_address:02x} -> {module_type}")

    @staticmethod
    def get_i2c_mappings():
        """Get all I2C address mappings."""
        return ModuleManager.i2c_module_mapping.copy()