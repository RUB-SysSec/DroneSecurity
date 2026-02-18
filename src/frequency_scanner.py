"""Frequency scanner for DJI DroneID Live Receiver.

This module manages frequency hopping and locking behavior for scanning
2.4 GHz and 5.8 GHz bands to detect DroneID signals.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
"""

from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bladerf_receiver import BladeRFReceiver


class ScanState(Enum):
    """State of the frequency scanner."""
    SCANNING = "scanning"
    LOCKED = "locked"


class FrequencyScanner:
    """Manages frequency scanning and locking for DroneID detection.
    
    The scanner cycles through predefined frequencies in the 2.4 GHz and 5.8 GHz
    bands. When a DroneID packet is detected, it locks to that frequency for
    continued reception. After 10 consecutive scans without detection, it
    resumes scanning all frequencies.
    
    Attributes:
        FREQUENCIES_2_4GHZ: List of 2.4 GHz frequencies to scan (Hz)
        FREQUENCIES_5_8GHZ: List of 5.8 GHz frequencies to scan (Hz)
        UNLOCK_THRESHOLD: Number of consecutive empty scans before unlocking
    """
    
    # 2.4 GHz frequencies (in Hz) - Requirement 2.1
    FREQUENCIES_2_4GHZ = [
        2414.5e6, 2429.5e6, 2434.5e6, 2444.5e6, 2459.5e6, 2474.5e6
    ]
    
    # 5.8 GHz frequencies (in Hz) - Requirement 2.2
    # Note: Can be disabled by setting FREQUENCIES_5_8GHZ = [] for 2.4 GHz only mode
    FREQUENCIES_5_8GHZ = [
        5721.5e6, 5731.5e6, 5741.5e6, 5756.5e6, 5761.5e6,
        5771.5e6, 5786.5e6, 5801.5e6, 5816.5e6, 5831.5e6
    ]
    
    # Number of consecutive empty scans before unlocking - Requirement 2.4
    UNLOCK_THRESHOLD = 10
    
    def __init__(self, receiver: Optional['BladeRFReceiver'] = None, 
                 duration: float = 1.3, sample_rate: float = 50e6,
                 band_2_4_only: bool = False):
        """Initialize frequency scanner.
        
        Args:
            receiver: BladeRFReceiver instance (optional, for standalone use)
            duration: Sample duration per frequency in seconds (default 1.3s)
            sample_rate: Sample rate in Hz (default 50 MHz)
            band_2_4_only: If True, only scan 2.4 GHz band (default False)
        """
        self.receiver = receiver
        self.duration = duration
        self.sample_rate = sample_rate
        
        # Combined frequency list for scanning
        if band_2_4_only:
            self._all_frequencies = self.FREQUENCIES_2_4GHZ.copy()
        else:
            self._all_frequencies = self.FREQUENCIES_2_4GHZ + self.FREQUENCIES_5_8GHZ
        
        # State machine variables
        self._state = ScanState.SCANNING
        self._locked_frequency: Optional[float] = None
        self._current_index = 0
        self._empty_scan_count = 0
    
    @property
    def state(self) -> ScanState:
        """Get current scanner state."""
        return self._state
    
    @property
    def locked_frequency(self) -> Optional[float]:
        """Get the currently locked frequency, or None if scanning."""
        return self._locked_frequency
    
    @property
    def all_frequencies(self) -> list:
        """Get list of all frequencies to scan."""
        return self._all_frequencies.copy()
    
    @property
    def empty_scan_count(self) -> int:
        """Get the count of consecutive empty scans while locked."""
        return self._empty_scan_count
    
    def lock_frequency(self, frequency: float) -> None:
        """Lock to a specific frequency after detection.
        
        When a DroneID packet is detected on a frequency, this method
        locks the scanner to that frequency for continued reception.
        
        Args:
            frequency: Frequency to lock to in Hz
            
        **Validates: Requirements 2.3**
        """
        self._state = ScanState.LOCKED
        self._locked_frequency = frequency
        self._empty_scan_count = 0
    
    def unlock_frequency(self) -> None:
        """Resume scanning all frequencies.
        
        This method unlocks the scanner and resumes cycling through
        all frequencies.
        
        **Validates: Requirements 2.4**
        """
        self._state = ScanState.SCANNING
        self._locked_frequency = None
        self._empty_scan_count = 0
    
    def record_detection(self, detected: bool) -> None:
        """Record whether a packet was detected on the current scan.
        
        This method updates the internal state based on detection results.
        If locked and no packet is detected, increments the empty scan counter.
        After UNLOCK_THRESHOLD consecutive empty scans, automatically unlocks.
        If a packet is detected while locked, resets the empty scan counter.
        
        Args:
            detected: True if a packet was detected, False otherwise
            
        **Validates: Requirements 2.3, 2.4**
        """
        if self._state == ScanState.LOCKED:
            if detected:
                # Reset counter on successful detection
                self._empty_scan_count = 0
            else:
                # Increment counter on empty scan
                self._empty_scan_count += 1
                
                # Check if we should unlock
                if self._empty_scan_count >= self.UNLOCK_THRESHOLD:
                    self.unlock_frequency()
    
    def get_next_frequency(self) -> float:
        """Get next frequency to scan.
        
        If locked, returns the locked frequency. Otherwise, cycles through
        all frequencies in order.
        
        Returns:
            Next frequency to scan in Hz
            
        **Validates: Requirements 2.3**
        """
        if self._state == ScanState.LOCKED and self._locked_frequency is not None:
            return self._locked_frequency
        
        # Get current frequency
        frequency = self._all_frequencies[self._current_index]
        
        # Advance to next frequency for next call
        self._current_index = (self._current_index + 1) % len(self._all_frequencies)
        
        return frequency
    
    def calculate_num_samples(self, duration: Optional[float] = None,
                               sample_rate: Optional[float] = None) -> int:
        """Calculate number of samples for a given duration.
        
        Args:
            duration: Duration in seconds (uses instance default if None)
            sample_rate: Sample rate in Hz (uses instance default if None)
            
        Returns:
            Number of samples to capture
            
        **Validates: Requirements 2.5**
        """
        dur = duration if duration is not None else self.duration
        rate = sample_rate if sample_rate is not None else self.sample_rate
        
        return int(dur * rate)
    
    def reset(self) -> None:
        """Reset scanner to initial state.
        
        Unlocks frequency and resets scan index to start.
        """
        self._state = ScanState.SCANNING
        self._locked_frequency = None
        self._current_index = 0
        self._empty_scan_count = 0
