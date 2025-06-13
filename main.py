# Updated main.py with simple sawtooth
import uasyncio as asyncio
import wifi.wifi_connect as wifi_connect
from module.module_manager import ModuleManager
from wifi.http_server import start_server
from ble.ble_simple_peripheral import receive_credentials
from utils.simple_sawtooth import start_sawtooth, stop_sawtooth, set_sawtooth_voltage_range

async def main():
    ip_address = None
    while ip_address is None:
        try:
            ip_address = wifi_connect.connect_to_wifi()
        except Exception as e:
            await receive_credentials()
    
    # Start sawtooth DAC
    set_sawtooth_voltage_range(0.45, 2.95)
    start_sawtooth(20000)  # 20kHz sawtooth on GP6-GP15

    # Initialize I2C
    ModuleManager.initialize_i2c(scl_pin=5, sda_pin=4)
    ModuleManager.set_i2c_scan_interval(0.5)
    
    await ModuleManager.load_modules()
    
    # Create async tasks
    i2c_detection_task = asyncio.create_task(ModuleManager.detect_i2c_modules())
    http_server_task = asyncio.create_task(start_server(ip_address))
    
    print("🚀 Starting I2C detection, HTTP server, and sawtooth DAC...")
    await asyncio.gather(i2c_detection_task, http_server_task)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    stop_sawtooth()
    print("Execution stopped by user")