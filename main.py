# Updated main.py
import uasyncio as asyncio
import wifi.wifi_connect as wifi_connect
from module.module_manager import ModuleManager  # Only need ModuleManager now
from wifi.http_server import start_server
from ble.ble_simple_peripheral import receive_credentials

async def main():
    ip_address = None
    while ip_address is None:
        try:
            ip_address = wifi_connect.connect_to_wifi()
        except Exception as e:
            receive_credentials()
    
    # Initialize I2C (optional - will auto-initialize if not done)
    ModuleManager.initialize_i2c(scl_pin=22, sda_pin=21)  # Customize pins if needed
    ModuleManager.set_i2c_scan_interval(0.5)  # Scan every 500ms
    
    await ModuleManager.load_modules()
    
    # Create async tasks
    i2c_detection_task = asyncio.create_task(ModuleManager.detect_i2c_modules())
    http_server_task = asyncio.create_task(start_server(ip_address))
    
    print("🚀 Starting I2C detection and HTTP server...")
    await asyncio.gather(i2c_detection_task, http_server_task)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Execution stopped by user")