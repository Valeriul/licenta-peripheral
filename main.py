import uasyncio as asyncio
import wifi_connect
from rezistance_detector import read_pins
from module_manager import ModuleManager
from http_server import start_server
from ble_simple_peripheral import receive_credentials

# bluetooth_handler = BluetoothHandler()

async def main():
    ip_address = None
    while ip_address is None:
        try:
            ip_address = wifi_connect.connect_to_wifi()
        except Exception as e:
            receive_credentials()
    await ModuleManager.load_modules()
    
    read_pins_task = asyncio.create_task(read_pins())
    http_server_task = asyncio.create_task(start_server(ip_address))
    
    await asyncio.gather(read_pins_task, http_server_task)  # Run both tasks concurrently

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Execution stopped by user")
