import network
import json
import time
import os

WIFI_CREDENTIALS_FILE = "wifi_credentials.json"

def connect_to_wifi():
    # Load credentials from JSON file
    with open(WIFI_CREDENTIALS_FILE, "r") as f:
        data = json.load(f)  # ✅ Uses json.load() instead of eval()

    ssid = data.get("ssid")
    password = data.get("password")

    if not ssid or not password:
        print("⚠️ Invalid WiFi credentials!")
        raise Exception("Invalid WiFi credentials")

    print(f"📡 Connecting to WiFi: {ssid}...")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    # Wait for connection with timeout
    timeout = 40  # seconds
    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print("❌ WiFi connection timeout!")
            raise Exception("WiFi connection timeout")
        time.sleep(1)

    ip = wlan.ifconfig()[0]
    print(f"✅ Connected to {ssid}, IP: {ip}")
    return ip

def get_ip_address():
    """Returns the current IP address."""
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    return "Not Connected"

def write_credentials(ssid, password, central_ip):
    """Writes WiFi credentials to a JSON file."""
    try:
        credentials = {
            "ssid": ssid,
            "password": password,
            "central_ip": central_ip
        }
        with open(WIFI_CREDENTIALS_FILE, "w") as f:
            json.dump(credentials, f)  # ✅ Uses json.dump()
        print("✅ WiFi credentials saved!")
    except Exception as e:
        print(f"⚠️ Error saving credentials: {e}")
