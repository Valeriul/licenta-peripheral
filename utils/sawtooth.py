from machine import Pin, Timer
import time

# Set up GPIO pins 6-12 as outputs
pins = []
for i in range(6, 13):
    pins.append(Pin(i, Pin.OUT))

# Configurable limits
LOWER_LIMIT = 15   # Minimum value (0-127)
UPPER_LIMIT = 127  # Maximum value (0-127)

# Global variables for timer-based sawtooth
timer_value = LOWER_LIMIT
timer_direction = 1
timer_active = True

def sawtooth_thread():
    """Thread-based sawtooth function"""
    value = LOWER_LIMIT
    direction = 1  # 1 for rising, -1 for falling

    while True:
        # Convert value to 7-bit binary and set pins
        for bit in range(7):
            pins[bit].value((value >> bit) & 1)

        # Update value for next step
        value += direction

        # Change direction at limits
        if value >= UPPER_LIMIT:
            direction = -1
        elif value <= LOWER_LIMIT:
            direction = 1

        time.sleep_us(10)  # 10μs delay - adjust as needed

def sawtooth_timer_callback(timer):
    """Timer callback function for sawtooth generation"""
    global timer_value, timer_direction, timer_active
    
    if not timer_active:
        return
    
    try:
        # Convert value to 7-bit binary and set pins
        for bit in range(7):
            pins[bit].value((timer_value >> bit) & 1)
        
        # Update value for next step
        timer_value += timer_direction
        
        # Change direction at limits
        if timer_value >= UPPER_LIMIT:
            timer_direction = -1
        elif timer_value <= LOWER_LIMIT:
            timer_direction = 1
    except:
        # Handle any exceptions silently in timer callback
        pass

def init_sawtooth_thread():
    """Initialize sawtooth generator using threading"""
    import _thread
    _thread.start_new_thread(sawtooth_thread, ())
    print("Sawtooth generator started using thread")

def init_sawtooth_timer():
    """Initialize sawtooth generator using timer"""
    global timer_active, timer_value, timer_direction
    timer_active = True
    timer_value = LOWER_LIMIT
    timer_direction = 1
    
    # Create timer with 100kHz frequency (10μs period)
    timer = Timer()
    timer.init(freq=100000, mode=Timer.PERIODIC, callback=sawtooth_timer_callback)
    print("Sawtooth generator started using timer")
    return timer

def stop_sawtooth_timer(timer):
    """Stop the timer-based sawtooth generator"""
    global timer_active
    timer_active = False
    time.sleep_ms(1)  # Give timer callback time to exit
    timer.deinit()
    
    # Set all pins to 0 when stopping
    for pin in pins:
        pin.value(0)
    print("Timer-based sawtooth generator stopped")

# Usage examples:
"""
# For thread-based sawtooth:
init_sawtooth_thread()

# For timer-based sawtooth:
timer = init_sawtooth_timer()
# ... do other work ...
stop_sawtooth_timer(timer)
"""