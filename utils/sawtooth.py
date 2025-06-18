from machine import Pin, Timer

class Sawtooth:
    def __init__(self, frequency=1.0):
        """
        Initialize sawtooth wave generator using GPIO pins 6-12 with Timer
        Args:
            frequency: Updates per second (Hz)
        """
        # Initialize GPIO pins 6-12 as outputs
        self.pins = []
        for pin_num in range(6, 13):  # pins 6 to 12 (7 pins total)
            self.pins.append(Pin(pin_num, Pin.OUT))
        
        self.frequency = frequency
        self.timer = Timer()
        
        # Counter state
        self.current_value = 0
        self.counting_up = True
        self.running = False
        
    def set_frequency(self, frequency):
        """Set the counting frequency in Hz"""
        self.frequency = frequency
        if self.running:
            # Restart timer with new frequency
            self.stop()
            self.start()
        
    def write_binary(self, decimal_value):
        """
        Write decimal value as binary to GPIO pins 6-12
        Pin 6 = LSB (bit 0), Pin 12 = MSB (bit 6)
        """
        for i in range(7):  # 7 pins (0-6 bit positions)
            bit_value = (decimal_value >> i) & 1
            self.pins[i].value(bit_value)
    
    def _timer_callback(self, timer):
        """
        Timer callback function - called at each timer interrupt
        """
        # Write current value to pins
        self.write_binary(self.current_value)
        
        # Update counter state
        if self.counting_up:
            if self.current_value >= 100:
                self.counting_up = False
                self.current_value = 99  # Start counting down from 99
            else:
                self.current_value += 1
        else:  # counting down
            if self.current_value <= 0:
                self.counting_up = True
                self.current_value = 1   # Start counting up from 1
            else:
                self.current_value -= 1
    
    def start(self):
        """
        Start the timer-based counter
        """
        if not self.running:
            # Calculate period in milliseconds
            period_ms = int(1000 / self.frequency)
            
            # Initialize timer with periodic mode
            self.timer.init(
                mode=Timer.PERIODIC,
                period=period_ms,
                callback=self._timer_callback
            )
            
            self.running = True
            print(f"Binary counter started at {self.frequency} Hz")
            print("GPIO Pin mapping:")
            print("Pin 6 (LSB) | Pin 7 | Pin 8 | Pin 9 | Pin 10 | Pin 11 | Pin 12 (MSB)")
        else:
            print("Counter is already running")
    
    def stop(self):
        """
        Stop the timer and turn off all pins
        """
        if self.running:
            self.timer.deinit()
            self.running = False
            
            # Turn off all pins
            for pin in self.pins:
                pin.value(0)
            
            print("Counter stopped")
        else:
            print("Counter is not running")
    
    def reset(self):
        """
        Reset counter to initial state (value = 0, counting up)
        """
        self.current_value = 0
        self.counting_up = True
        if not self.running:
            self.write_binary(0)  # Update pins if not running
    
    def get_status(self):
        """
        Get current counter status
        """
        direction = "UP" if self.counting_up else "DOWN"
        status = "RUNNING" if self.running else "STOPPED"
        return {
            'value': self.current_value,
            'direction': direction,
            'frequency': self.frequency,
            'status': status
        }
    
    def single_cycle(self):
        """
        Perform exactly one complete cycle: 0->100->0 then stop
        """
        if self.running:
            print("Stop the continuous counter first")
            return
        
        self.reset()
        cycle_complete = False
        
        def cycle_callback(timer):
            nonlocal cycle_complete
            
            # Write current value to pins
            self.write_binary(self.current_value)
            
            # Check if we completed a full cycle
            if not self.counting_up and self.current_value == 0:
                cycle_complete = True
                self.stop()
                return
            
            # Update counter state
            if self.counting_up:
                if self.current_value >= 100:
                    self.counting_up = False
                    self.current_value = 99
                else:
                    self.current_value += 1
            else:  # counting down
                self.current_value -= 1
        
        # Start timer for single cycle
        period_ms = int(1000 / self.frequency)
        self.timer.init(
            mode=Timer.PERIODIC,
            period=period_ms,
            callback=cycle_callback
        )
        
        print(f"Running single cycle at {self.frequency} Hz...")