# This example demonstrates a UART periperhal.

# This example demonstrates the low-level bluetooth module. For most
# applications, we recommend using the higher-level aioble library which takes
# care of all IRQ handling and connection management. See
# https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble

import bluetooth
import time
import wifi.wifi_connect as wifi_connect
import random
from ble.ble_advertising import advertising_payload

from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)



class BLESimplePeripheral:  
    def __init__(self, ble, name="LICN-"+str(random.randint(10, 99))):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback


async def receive_credentials():
    ble = bluetooth.BLE()
    p = BLESimplePeripheral(ble)

    stop = False
    ssid = None
    password = None
    central_ip = None

    def on_rx(v):
        """Handles incoming BLE messages and stores data."""
        print("Received:", v)

        try:
            # Decode bytes and split the message
            label, content = v.decode().strip().split(":", 1)

            # Ensure we access the variables from the outer scope
            nonlocal ssid, password, central_ip, stop

            # Store received values
            if label == "SSID":
                ssid = content.strip()
            elif label == "PASSWORD":
                password = content.strip()
            elif label == "IP":
                central_ip = content.strip()

            # Check if all values are received
            if ssid and password and central_ip:
                stop = True

        except Exception as e:
            print(f"Error processing received data: {e}")


    p.on_write(on_rx)

    print("Waiting for data...")
    while stop is False:
        time.sleep_ms(100)  # Block until data is received
        
    ble.active(False)
    
    wifi_connect.write_credentials(ssid, password, central_ip)
