import network

def connect_to_wifi(SSID, PASSWORD):
    """Conectează Pico W la WiFi și returnează IP-ul"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        pass

    ip = wlan.ifconfig()[0]
    print(f"Conectat la: {ip}")
    return ip
