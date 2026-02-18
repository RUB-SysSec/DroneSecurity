"""Configuration dataclasses for the DJI DroneID Live Receiver."""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class ReceiverConfig:
    """Configuration for the DroneID receiver.
    
    Attributes:
        sample_rate: Sample rate in Hz (default 50 MHz)
        gain: RX gain in dB (-15 to 60), None for AGC
        duration: Sample duration per frequency in seconds
        num_workers: Number of worker processes for parallel processing
        debug: Enable debug output
        legacy: Support legacy drones (Mavic Pro, Mavic 2)
        packet_type: Type of packet to detect (droneid, c2, beacon, video)
        fast: Fast mode - skip file writing for maximum speed
    """
    sample_rate: float = 50e6
    gain: Optional[int] = None  # None = AGC
    duration: float = 1.3  # seconds per frequency
    num_workers: int = 2
    debug: bool = False
    legacy: bool = False
    packet_type: str = "droneid"
    fast: bool = False


@dataclass
class SampleBuffer:
    """Container for received samples with metadata.
    
    Attributes:
        samples: Complex64 IQ samples
        frequency: Center frequency in Hz
        timestamp: Reception timestamp
    """
    samples: np.ndarray  # complex64 IQ samples
    frequency: float  # center frequency in Hz
    timestamp: float  # reception timestamp


@dataclass
class StreamConfig:
    """BladeRF synchronous stream configuration.
    
    Attributes:
        num_buffers: Number of buffers for streaming
        buffer_size: Size of each buffer in samples
        num_transfers: Number of USB transfers
        stream_timeout: Stream timeout in milliseconds
    """
    num_buffers: int = 16
    buffer_size: int = 8192
    num_transfers: int = 8
    stream_timeout: int = 3500  # ms
