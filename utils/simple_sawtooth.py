# simple_sawtooth.py - Simple Pi Pico W Sawtooth DAC with Voltage Control
from machine import Pin, Timer, mem32
import micropython

# Enable emergency exception buffer for interrupt safety
micropython.alloc_emergency_exception_buf(100)

class SimpleSawtooth:
    def __init__(self, vref=3.3):
        # Setup pins GP6 to GP15 for 10-bit DAC (using mem32 for speed)
        for pin_num in range(6, 16):
            Pin(pin_num, Pin.OUT)
        
        self.vref = vref           # Reference voltage (typically 3.3V for Pi Pico)
        self.dac_max = 1023       # 10-bit DAC maximum count
        
        self.current_val = 0
        self.min_volts = 0.0      # Minimum voltage
        self.max_volts = vref     # Maximum voltage
        self.min_dac = 0          # Corresponding DAC values
        self.max_dac = 1023
        self.step_size = 32
        self.timer = Timer()
        self.running = False
        self.current_freq = 1000
    
    def volts_to_dac(self, volts):
        """Convert voltage to DAC count"""
        # Clamp voltage to valid range
        volts = max(0.0, min(self.vref, volts))
        return int((volts / self.vref) * self.dac_max)
    
    def dac_to_volts(self, dac_val):
        """Convert DAC count to voltage"""
        return (dac_val / self.dac_max) * self.vref
    
    def write_r2r_fast(self, val):
        """Fast R-2R output using direct register access"""
        # Clamp value to valid 10-bit range (0-1023)
        val = max(0, min(1023, val))
        # Clear GP6-GP15 bits
        mem32[0xD0000018] = 0x3FF << 6
        # Set GP6-GP15 with new value
        mem32[0xD0000014] = (val & 0x3FF) << 6
    
    def timer_callback(self, timer):
        """Timer interrupt callback - increment sawtooth"""
        self.write_r2r_fast(self.current_val)
        self.current_val += self.step_size
        if self.current_val > self.max_dac:
            self.current_val = self.min_dac
    
    def set_voltage_range(self, min_volts=0.0, max_volts=None):
        """Set the min and max voltages for the sawtooth wave"""
        if max_volts is None:
            max_volts = self.vref
        
        # Ensure values are within valid voltage range
        self.min_volts = max(0.0, min(self.vref, min_volts))
        self.max_volts = max(0.0, min(self.vref, max_volts))
        
        # Ensure min is less than max
        if self.min_volts >= self.max_volts:
            self.max_volts = self.min_volts + 0.01  # 10mV minimum difference
            if self.max_volts > self.vref:
                self.max_volts = self.vref
                self.min_volts = self.vref - 0.01
        
        # Convert to DAC values
        self.min_dac = self.volts_to_dac(self.min_volts)
        self.max_dac = self.volts_to_dac(self.max_volts)
        
        # If currently running, restart with new range
        if self.running:
            freq = self.current_freq
            self.stop()
            self.start(freq)
    
    def start(self, freq_hz=1000):
        """Start sawtooth at frequency"""
        if self.running:
            self.stop()
        
        try:
            # Store frequency for potential restarts
            self.current_freq = freq_hz
            
            # Calculate step size based on current DAC range
            range_size = self.max_dac - self.min_dac
            self.step_size = max(1, range_size // 32)  # At least 1, up to 32 steps per cycle
            
            self.current_val = self.min_dac
            
            # Use the exact format from your working code
            self.timer = Timer()
            self.timer.init(freq=freq_hz, mode=Timer.PERIODIC, callback=self.timer_callback)
            
            self.running = True
            
        except Exception as e:
            self.running = False
    
    def stop(self):
        """Stop sawtooth"""
        if self.running:
            self.timer.deinit()
            self.write_r2r_fast(self.min_dac)  # Reset to minimum voltage
            self.current_val = self.min_dac
            self.running = False
    
    def get_voltage_range(self):
        """Get current min and max voltages"""
        return self.min_volts, self.max_volts
    
    def get_current_voltage(self):
        """Get current output voltage"""
        return self.dac_to_volts(self.current_val)
    
    def set_reference_voltage(self, vref):
        """Set the reference voltage (e.g., 3.3V, 5.0V)"""
        self.vref = vref
        # Update voltage range to maintain the same DAC values
        self.min_volts = self.dac_to_volts(self.min_dac)
        self.max_volts = self.dac_to_volts(self.max_dac)

# Global instance (default 3.3V reference)
sawtooth = SimpleSawtooth(vref=3.3)

def start_sawtooth(freq=1000):
    """Start sawtooth wave"""
    sawtooth.start(freq)

def stop_sawtooth():
    """Stop sawtooth wave"""
    sawtooth.stop()

def set_sawtooth_voltage_range(min_volts=0.0, max_volts=3.3):
    """Set the min and max voltages for the sawtooth wave"""
    sawtooth.set_voltage_range(min_volts, max_volts)

def get_sawtooth_voltage_range():
    """Get current sawtooth min and max voltages"""
    return sawtooth.get_voltage_range()

def get_current_voltage():
    """Get current output voltage"""
    return sawtooth.get_current_voltage()

def set_reference_voltage(vref):
    """Set DAC reference voltage"""
    sawtooth.set_reference_voltage(vref)

# Example usage:
# set_sawtooth_voltage_range(0.5, 2.8)  # Set sawtooth from 0.5V to 2.8V
# start_sawtooth(1000)                  # Start 1kHz sawtooth within that range
# print(f"Range: {get_sawtooth_voltage_range()} V")
# print(f"Current: {get_current_voltage():.3f} V")