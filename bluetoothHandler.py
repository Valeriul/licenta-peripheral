import uasyncio as asyncio
import bluetooth
import struct
import random
import network
import json
import wifi_connect

CREDENTIALS_FILE = "wifi_credentials.json"

class BluetoothHandler:

    def __init__(self):
        self.bt = bluetooth.BLE()
        self.bt.active(True)
        self.credentials_event = asyncio.Event()
        self.SSID = None
        self.PASSWORD = None

        self.device_name = f"LICN-{random.randint(10000, 99999)}"
        self.uuid_service = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
        self.uuid_rx = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
        self.uuid_tx = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef2")

        # Define characteristics with properties and permissions
        self.rx_char = (self.uuid_rx, bluetooth.FLAG_WRITE)
        self.tx_char = (self.uuid_tx, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY)
        self.tx_rx_service = (self.uuid_service, [self.rx_char, self.tx_char])

        # Register services correctly
        self.services = [self.tx_rx_service]
        ((self.rx_handle, self.tx_handle),) = self.bt.gatts_register_services(self.services)

        self.bt.config(gap_name=self.device_name)
        self.bt.irq(self.bt_callback)
        self.start_advertising()

    def start_advertising(self):
        print(f"Starting Bluetooth advertising as {self.device_name}")
        self.bt.gap_advertise(100, b"\x02\x01\x06" + struct.pack("<B", len(self.device_name) + 1) + b"\x09" + self.device_name.encode())

    def get_ip_address(self):
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            return wlan.ifconfig()[0]
        return "0.0.0.0"
    
    def save_credentials(self):
        """Save received credentials to a file."""
        if self.SSID and self.PASSWORD:
            with open(CREDENTIALS_FILE, "w") as f:
                json.dump({"ssid": self.SSID, "password": self.PASSWORD}, f)
            print("WiFi credentials saved successfully.")
    
    def load_credentials(self):
        """Load WiFi credentials from a file if available."""
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                json_data = json.load(f)
                if(json_data.get("ssid") and json_data.get("password")):
                    self.SSID=json_data.get("ssid")
                    self.PASSWORD=json_data.get("password")
                    print("WiFi credentials loaded successfully.")
        except (OSError, ValueError):
            print("No saved WiFi credentials found.")

    def bt_callback(self, event, data):
        """Handles Bluetooth write events."""
        if event == bluetooth._IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data[:2]
            received_data = self.bt.gatts_read(attr_handle).decode("utf-8")
            print(f"Received Bluetooth data: {received_data}")

            if not received_data:
                print("No valid data received.")
                return

            try:
                ssid, password, central_url = received_data.split("|")

                if ssid and password:
                    self.SSID = ssid.strip()
                    self.PASSWORD = password.strip()
                    self.save_credentials()
                    print("Setting event to notify credentials received.")
                    self.credentials_event.set()

                    # Send back the IP address
                    ip_address = wifi_connect.connect_to_wifi(self.SSID, self.PASSWORD)
                    print(f"Connected to WiFi. Sending IP: {ip_address}")
                    self.bt.gatts_write(self.tx_handle, ip_address.encode())
                else:
                    print("Received invalid credentials. Ignoring.")
            except ValueError:
                print("Invalid Bluetooth data format")

    async def wait_for_credentials(self):
        """Waits for credentials to be received via Bluetooth."""
        print("Waiting for Bluetooth credentials...")
        self.load_credentials()
        
        if self.SSID and self.PASSWORD:
            print("Loaded saved credentials.")
            return self.get_ip_address()

        while True:
            print("Still waiting for credentials...")
            await self.credentials_event.wait()
            if self.SSID and self.PASSWORD:
                print("Credentials received and validated!")
                return self.get_ip_address()
            print("Event triggered but credentials still not set. Continuing to wait.")
