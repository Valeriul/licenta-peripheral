import network
import json
import time
import os

WIFI_CREDENTIALS_FILE = "wifi_credentials.json"

def connect_to_wifi():
    # Load credentials from JSON file
    with open(WIFI_CREDENTIALS_FILE, "r") as f:
        data = json.load(f)

    ssid = data.get("ssid")
    password = data.get("password")

    if not ssid or not password:
        print("⚠️ Invalid WiFi credentials!")
        raise Exception("Invalid WiFi credentials")

    print(f"📡 Connecting to WiFi: {ssid}...")

    # Setup WiFi interface for Android hotspot compatibility
    wlan = network.WLAN(network.STA_IF)
    
    # Ensure AP mode is disabled
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        ap_if.active(False)
    
    wlan.active(True)
    time.sleep(2)  # Critical: Allow chip initialization
    
    # Configure for optimal Android hotspot compatibility
    network.country('US')  # Set country code for proper channel access
    wlan.config(pm=0xa11140)  # Disable power management for stability
    
    # Connection strategies with exponential backoff
    max_attempts = 5
    for attempt in range(max_attempts):
        print(f"🔄 Connection attempt {attempt + 1}/{max_attempts}")
        
        # Verify network is visible
        if not _verify_network_visibility(wlan, ssid):
            print(f"⚠️ Network '{ssid}' not found in scan")
            time.sleep(2)
            continue
        
        # Clean connection state
        if wlan.isconnected():
            wlan.disconnect()
            time.sleep(1)
        
        try:
            # Try different connection strategies
            strategies = [
                lambda: wlan.connect(ssid, password),
                lambda: wlan.connect(ssid, password, channel=6),  # Force channel 6
                lambda: wlan.connect(ssid, password, channel=1),  # Try channel 1
            ]
            
            strategy_index = min(attempt, len(strategies) - 1)
            strategies[strategy_index]()
            
            # Wait for connection with increasing timeout
            timeout = 20 + (attempt * 5)  # 20, 25, 30, 35, 40 seconds
            if _wait_for_connection(wlan, timeout):
                ip = wlan.ifconfig()[0]
                print(f"✅ Connected to {ssid}, IP: {ip}")
                return ip
                
        except OSError as e:
            print(f"⚠️ Connection error: {e}")
        
        # Exponential backoff (capped at 16 seconds)
        if attempt < max_attempts - 1:
            delay = min(2 ** attempt, 16)
            print(f"⏳ Waiting {delay}s before retry...")
            time.sleep(delay)
    
    print("❌ WiFi connection failed after all attempts!")
    raise Exception("WiFi connection failed after all attempts")

def _verify_network_visibility(wlan, target_ssid):
    """Verify target network is detectable and check signal strength"""
    try:
        networks = wlan.scan()
        for net in networks:
            ssid_name = net[0].decode()
            if ssid_name == target_ssid:
                rssi = net[3]
                channel = net[2]
                security = net[4]
                
                print(f"📶 Found network: Ch{channel}, {rssi}dBm, Sec{security}")
                
                if rssi < -80:
                    print(f"⚠️ Weak signal ({rssi} dBm) - may cause issues")
                if channel > 11:
                    print(f"⚠️ Channel {channel} may not be fully supported")
                    
                return True
    except Exception as e:
        print(f"⚠️ Network scan error: {e}")
    return False

def _wait_for_connection(wlan, timeout_seconds):
    """Wait for connection with detailed status monitoring"""
    start_time = time.ticks_ms()
    
    while not wlan.isconnected():
        elapsed = time.ticks_diff(time.ticks_ms(), start_time)
        if elapsed > timeout_seconds * 1000:
            status = wlan.status()
            print(f"⏰ Timeout after {timeout_seconds}s (Status: {_decode_status(status)})")
            return False
        
        status = wlan.status()
        if status < 0:  # Error condition
            print(f"❌ Connection failed: {_decode_status(status)}")
            return False
        
        # Show progress every 5 seconds
        if elapsed % 5000 < 500:  # Print roughly every 5 seconds
            print(f"🔄 Connecting... ({_decode_status(status)})")
        
        time.sleep(0.5)
    
    return True

def _decode_status(status):
    """Convert status codes to readable messages"""
    status_codes = {
        -3: "Wrong password/WPA3 incompatibility",
        -2: "No access point found", 
        -1: "Connection failed",
        0: "Idle",
        1: "Connecting",
        3: "Connected"
    }
    return status_codes.get(status, f"Unknown ({status})")

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
            json.dump(credentials, f)
        print("✅ WiFi credentials saved!")
    except Exception as e:
        print(f"⚠️ Error saving credentials: {e}")