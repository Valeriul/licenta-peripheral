import machine

def getBatteryPercentage():
    # GPIO26 is ADC0 on the Pico
    adc = machine.ADC(0)
    
    # Read raw ADC value (0-65535 for 16-bit ADC)
    raw_reading = adc.read_u16()
    
    # Convert to voltage at GPIO26 (3.3V reference)
    gpio_voltage = (raw_reading / 65535) * 3.3
    
    # Calculate actual battery voltage using voltage divider
    # gpio_voltage = battery_voltage * (2.2 / (1 + 2.2))
    battery_voltage = gpio_voltage * (3.2 / 2.2)
    
    # Define Li-Po battery voltage range with PCM protection
    min_voltage = 3.0  # PCM cutoff voltage (0% usable charge)
    max_voltage = 4.2  # Full charge voltage (100% charge)
    
    # Calculate percentage using linear interpolation
    percentage = ((battery_voltage - min_voltage) / (max_voltage - min_voltage)) * 100
    
    # Clamp between 0 and 100
    percentage = max(0, min(100, percentage))
    
    return int(percentage)