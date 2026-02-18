"""BladeRF A4 hardware interface for DJI DroneID Live Receiver.

This module provides a hardware abstraction layer for the BladeRF A4 SDR,
using GNU Radio's osmosdr for device access with persistent streaming.
"""

import numpy as np
from typing import Optional
import threading
import queue
import time

from config import StreamConfig


class DeviceNotFoundError(Exception):
    """Raised when BladeRF device is not found."""
    pass


class DeviceBusyError(Exception):
    """Raised when BladeRF device is busy or in use."""
    pass


class ConfigurationError(Exception):
    """Raised when configuration parameters are invalid."""
    pass


class BladeRFReceiver:
    """Hardware interface for BladeRF A4 SDR using GNU Radio osmosdr.
    
    This class provides methods for initializing the BladeRF A4 device,
    configuring frequency and gain, and receiving IQ samples.
    
    Uses a persistent streaming approach for real-time performance.
    """
    
    # BladeRF A4 frequency range
    MIN_FREQUENCY = 70e6      # 70 MHz
    MAX_FREQUENCY = 6000e6    # 6 GHz
    
    # BladeRF A4 gain range
    MIN_GAIN = -15
    MAX_GAIN = 60
    
    # Supported sample rates
    MIN_SAMPLE_RATE = 520834   # ~521 kHz
    MAX_SAMPLE_RATE = 61.44e6  # 61.44 MHz
    
    def __init__(self, sample_rate: float = 50e6, gain: Optional[int] = None,
                 stream_config: Optional[StreamConfig] = None):
        """Initialize BladeRF A4 device using osmosdr with persistent streaming.
        
        Args:
            sample_rate: Sample rate in Hz (default 50 MHz)
            gain: RX gain in dB (-15 to 60), None for AGC
            stream_config: Stream configuration (unused with osmosdr)
        """
        self.sample_rate = sample_rate
        self.gain = gain
        self.stream_config = stream_config or StreamConfig()
        self.source = None
        self._current_frequency = None
        
        # Streaming state
        self._tb = None
        self._sink = None
        self._streaming = False
        self._stream_lock = threading.Lock()
        
        self._validate_sample_rate(sample_rate)
        if gain is not None:
            self._validate_gain(gain)
        
        self._initialize_device()

    def _validate_sample_rate(self, sample_rate: float) -> None:
        """Validate sample rate is within supported range."""
        if not self.MIN_SAMPLE_RATE <= sample_rate <= self.MAX_SAMPLE_RATE:
            raise ConfigurationError(
                f"Sample rate {sample_rate/1e6:.2f} MHz is out of range. "
                f"Supported range: {self.MIN_SAMPLE_RATE/1e6:.2f} MHz to "
                f"{self.MAX_SAMPLE_RATE/1e6:.2f} MHz"
            )
    
    def _validate_gain(self, gain: int) -> None:
        """Validate gain is within supported range."""
        if not self.MIN_GAIN <= gain <= self.MAX_GAIN:
            raise ConfigurationError(
                f"Gain {gain} dB is out of range. "
                f"Supported range: {self.MIN_GAIN} dB to {self.MAX_GAIN} dB"
            )
    
    def _validate_frequency(self, frequency: float) -> None:
        """Validate frequency is within supported range."""
        if not self.MIN_FREQUENCY <= frequency <= self.MAX_FREQUENCY:
            raise ConfigurationError(
                f"Frequency {frequency/1e6:.2f} MHz is out of range. "
                f"Supported range: {self.MIN_FREQUENCY/1e6:.2f} MHz to "
                f"{self.MAX_FREQUENCY/1e6:.2f} MHz"
            )
    
    def _initialize_device(self) -> None:
        """Initialize and configure the BladeRF device using osmosdr."""
        try:
            import osmosdr
            from gnuradio import gr
        except ImportError as e:
            raise DeviceNotFoundError(
                "GNU Radio osmosdr not found. "
                "Please install GNU Radio with osmosdr support.\n"
                f"Error: {e}"
            )
        
        try:
            # Create osmosdr source - bladerf=0 explicitly selects BladeRF
            self.source = osmosdr.source(args="numchan=1 bladerf=0")
            
            # Configure sample rate
            self.source.set_sample_rate(self.sample_rate)
            
            # Set initial frequency
            self.source.set_center_freq(2414.5e6, 0)
            self._current_frequency = 2414.5e6
            
            # Configure gain
            if self.gain is None:
                self.source.set_gain_mode(True, 0)
            else:
                self.source.set_gain_mode(False, 0)
                self.source.set_gain(self.gain, 0)
                self.source.set_if_gain(20, 0)
                self.source.set_bb_gain(20, 0)
            
            # Set bandwidth
            self.source.set_bandwidth(self.sample_rate / 2, 0)
            
            # No frequency correction
            self.source.set_freq_corr(0, 0)
            
            # DC offset and IQ balance
            self.source.set_dc_offset_mode(0, 0)
            self.source.set_iq_balance_mode(0, 0)
            
            print(f"BladeRF initialized: {self.sample_rate/1e6:.2f} MHz sample rate")
            
        except Exception as e:
            error_msg = str(e).lower()
            if "no device" in error_msg or "not found" in error_msg or "failed" in error_msg:
                raise DeviceNotFoundError(
                    "BladeRF A4 device not found. Please check:\n"
                    "1. Device is connected via USB\n"
                    "2. USB drivers are installed\n"
                    "3. No other application is using the device\n"
                    f"Error: {e}"
                )
            elif "busy" in error_msg or "in use" in error_msg:
                raise DeviceBusyError(
                    "BladeRF device is busy or in use by another application."
                )
            else:
                raise DeviceNotFoundError(f"Failed to open BladeRF device: {e}")

    def set_frequency(self, frequency: float) -> bool:
        """Set center frequency.
        
        Includes settling time for PLL lock and filter stabilization.
        BladeRF A4 typically needs 10-50ms to settle after frequency change.
        Includes retry logic for USB communication failures.
        """
        self._validate_frequency(frequency)
        
        # Retry logic for USB communication failures
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.source.set_center_freq(frequency, 0)
                self._current_frequency = frequency
                # BladeRF needs time for PLL to lock and filters to settle
                # 100ms is more conservative for stability
                time.sleep(0.100)
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Frequency set failed (attempt {attempt+1}/{max_retries}), retrying...")
                    time.sleep(0.200)  # Wait before retry
                else:
                    print(f"Failed to set frequency after {max_retries} attempts: {e}")
                    return False
    
    def set_gain(self, gain: Optional[int]) -> bool:
        """Set RX gain."""
        if gain is not None:
            self._validate_gain(gain)
        
        try:
            if gain is None:
                self.source.set_gain_mode(True, 0)
            else:
                self.source.set_gain_mode(False, 0)
                self.source.set_gain(gain, 0)
            self.gain = gain
            return True
        except Exception as e:
            print(f"Failed to set gain: {e}")
            return False

    def receive_samples(self, num_samples: int, discard_initial: int = None) -> np.ndarray:
        """Receive IQ samples from the SDR using a fresh flowgraph each time.
        
        This approach ensures clean sample capture without buffer issues.
        Discards initial samples to avoid transients from frequency switching.
        
        Args:
            num_samples: Number of complex samples to receive
            discard_initial: Number of initial samples to discard (default: 10ms worth)
            
        Returns:
            Complex64 numpy array of IQ samples
        """
        from gnuradio import gr, blocks
        
        # Default: discard 10ms of samples to avoid frequency switch transients
        if discard_initial is None:
            discard_initial = int(self.sample_rate * 0.010)  # 10ms
        
        total_samples = num_samples + discard_initial
        
        with self._stream_lock:
            try:
                # Create a simple flowgraph for sample capture
                tb = gr.top_block("Sample Capture", catch_exceptions=True)
                
                # Vector sink to collect samples
                sink = blocks.vector_sink_c()
                
                # Head block to limit samples
                head = blocks.head(gr.sizeof_gr_complex, total_samples)
                
                # Connect: source -> head -> sink
                tb.connect(self.source, head, sink)
                
                # Run the flowgraph (blocks until num_samples received)
                tb.run()
                tb.wait()
                
                # Get samples and discard initial transients
                all_samples = np.array(sink.data(), dtype=np.complex64)
                samples = all_samples[discard_initial:]
                
                # Disconnect and cleanup
                tb.disconnect_all()
                del tb
                
                return samples
                
            except Exception as e:
                print(f"Error receiving samples: {e}")
                import traceback
                traceback.print_exc()
                return np.array([], dtype=np.complex64)
    
    def receive_samples_fast(self, num_samples: int) -> np.ndarray:
        """Receive IQ samples using direct buffer access for better performance.
        
        This method uses a circular buffer approach for faster sample capture.
        
        Args:
            num_samples: Number of complex samples to receive
            
        Returns:
            Complex64 numpy array of IQ samples
        """
        from gnuradio import gr, blocks
        
        # Use smaller chunks for more responsive capture
        chunk_size = min(num_samples, int(self.sample_rate * 0.1))  # 100ms chunks max
        samples_collected = []
        samples_remaining = num_samples
        
        with self._stream_lock:
            try:
                while samples_remaining > 0:
                    current_chunk = min(chunk_size, samples_remaining)
                    
                    # Create flowgraph for this chunk
                    tb = gr.top_block("Chunk Capture", catch_exceptions=True)
                    sink = blocks.vector_sink_c()
                    head = blocks.head(gr.sizeof_gr_complex, current_chunk)
                    
                    tb.connect(self.source, head, sink)
                    tb.run()
                    tb.wait()
                    
                    chunk_samples = np.array(sink.data(), dtype=np.complex64)
                    samples_collected.append(chunk_samples)
                    samples_remaining -= len(chunk_samples)
                    
                    tb.disconnect_all()
                    del tb
                    
                    if len(chunk_samples) == 0:
                        break
                
                if samples_collected:
                    return np.concatenate(samples_collected)
                return np.array([], dtype=np.complex64)
                
            except Exception as e:
                print(f"Error receiving samples: {e}")
                return np.array([], dtype=np.complex64)
    
    @staticmethod
    def _convert_sc16_q11_to_complex64(buf: bytearray) -> np.ndarray:
        """Convert SC16_Q11 formatted samples to complex64."""
        raw_samples = np.frombuffer(buf, dtype=np.int16)
        i_samples = raw_samples[0::2].astype(np.float32)
        q_samples = raw_samples[1::2].astype(np.float32)
        scale_factor = 2048.0
        i_samples /= scale_factor
        q_samples /= scale_factor
        samples = i_samples + 1j * q_samples
        return samples.astype(np.complex64)
    
    def close(self) -> None:
        """Release hardware resources."""
        with self._stream_lock:
            self._streaming = False
            if self._tb is not None:
                try:
                    self._tb.stop()
                    self._tb.wait()
                except:
                    pass
                self._tb = None
            self.source = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def __del__(self):
        self.close()
