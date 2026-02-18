#!/usr/bin/python3
"""DJI DroneID Live Receiver using BladeRF A4 SDR.

This module provides real-time reception and decoding of DJI DroneID signals
using BladeRF A4 hardware on Windows.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 5.2, 5.4, 6.1, 6.2, 6.5, 8.1-8.6**
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import queue
import numpy as np
import signal
import argparse
import threading
import multiprocessing as mp
import time
import json
from datetime import datetime
from pathlib import Path
import warnings

from bladerf_receiver import BladeRFReceiver, DeviceNotFoundError, DeviceBusyError, ConfigurationError
from frequency_scanner import FrequencyScanner, ScanState
from config import ReceiverConfig
from path_utils import (
    create_decoded_bits_filepath,
    create_raw_samples_filepath,
    create_debug_samples_filepath,
    safe_write_bytes,
    normalize_path,
    create_empty_file
)
import SpectrumCapture as SC
from Packet import Packet
from qpsk import Decoder
from droneid_packet import DroneIDPacket

warnings.filterwarnings("ignore")

# Global state
sample_queue: mp.Queue = None
detection_queue: mp.Queue = None  # For workers to signal detections
exit_event: threading.Event = None
receiver: BladeRFReceiver = None
db_filename: Path = None
raw_samples_filename: Path = None
debug_samples_filename: Path = None
args: argparse.Namespace = None
session_timestamp: datetime = None

# Statistics
num_decoded = 0
crc_err = 0
correct_pkt = 0
total_num_pkt = 0


def reset_statistics() -> None:
    """Reset all statistics counters to zero.
    
    Useful for testing and when starting a new session.
    
    **Validates: Requirements 7.4**
    """
    global num_decoded, crc_err, correct_pkt, total_num_pkt
    num_decoded = 0
    crc_err = 0
    correct_pkt = 0
    total_num_pkt = 0


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
        
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6**
    """
    parser = argparse.ArgumentParser(
        description="DJI DroneID Live Receiver using BladeRF A4 SDR",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '-g', '--gain',
        default=30,
        type=int,
        help="RX gain in dB (0 for AGC, 1-60 for manual gain)"
    )
    
    parser.add_argument(
        '-s', '--sample_rate',
        default=50e6,
        type=float,
        help="Sample rate in Hz (default 50 MHz)"
    )
    
    parser.add_argument(
        '-w', '--workers',
        default=2,
        type=int,
        help="Number of worker processes for parallel signal processing"
    )
    
    parser.add_argument(
        '-t', '--duration',
        default=0.8,
        type=float,
        help="Duration in seconds to capture samples per frequency band"
    )
    
    parser.add_argument(
        '-d', '--debug',
        default=False,
        action="store_true",
        help="Enable debug output with additional processing information"
    )
    
    parser.add_argument(
        '-v', '--verbose',
        default=False,
        action="store_true",
        help="Enable verbose output showing processing stages"
    )
    
    parser.add_argument(
        '-l', '--legacy',
        default=False,
        action="store_true",
        help="Support legacy drones (Mavic Pro, Mavic 2)"
    )
    
    parser.add_argument(
        '-p', '--packettype',
        default="droneid",
        type=str,
        choices=["droneid", "c2", "beacon", "video"],
        help="Packet type to detect"
    )
    
    parser.add_argument(
        '--save-files',
        default=False,
        action="store_true",
        help="Enable file saving (decoded bits, raw samples, debug samples). Disabled by default for maximum speed."
    )
    
    parser.add_argument(
        '--band-2-4-only',
        default=False,
        action="store_true",
        help="Only scan 2.4 GHz band (skip 5.8 GHz frequencies)"
    )
    
    parser.add_argument(
        '--output-dir',
        default=None,
        type=str,
        help="Output directory for files (default: src folder). Use RAM disk path for faster I/O (e.g., R:\\droneid)"
    )
    
    return parser


def parse_arguments(arg_list=None) -> argparse.Namespace:
    """Parse command line arguments.
    
    Args:
        arg_list: Optional list of arguments (for testing), uses sys.argv if None
        
    Returns:
        Parsed arguments namespace
    """
    parser = create_argument_parser()
    return parser.parse_args(arg_list)


def get_receiver_config(args: argparse.Namespace) -> ReceiverConfig:
    """Convert parsed arguments to ReceiverConfig.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        ReceiverConfig instance
    """
    gain = None if args.gain == 0 else args.gain
    
    return ReceiverConfig(
        sample_rate=args.sample_rate,
        gain=gain,
        duration=args.duration,
        num_workers=args.workers,
        debug=args.debug,
        legacy=args.legacy,
        packet_type=args.packettype,
        fast=not args.save_files  # Inverted: fast mode when NOT saving files
    )


def signal_handler(sig, frame):
    """Handle interrupt signals for clean shutdown.
    
    **Validates: Requirements 5.4, 6.5**
    """
    global exit_event
    if exit_event is not None:
        exit_event.set()


def setup_signal_handlers():
    """Set up signal handlers for Windows compatibility.
    
    **Validates: Requirements 5.4**
    """
    # SIGINT works on Windows for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # SIGTERM is not available on Windows, only set if available
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)


def decoded_to_file(raw_bits: bytes, filepath: Path) -> None:
    """Save decoded bits to a binary file.
    
    Args:
        raw_bits: Raw decoded bits
        filepath: Output file path
        
    **Validates: Requirements 5.3, 7.3**
    """
    if len(raw_bits) > 0:
        safe_write_bytes(filepath, raw_bits, append=True)


def format_output_json(payload: DroneIDPacket, frequency: float = None) -> str:
    """Format DroneID payload as valid JSON with timestamp.
    
    Args:
        payload: Decoded DroneID packet
        frequency: Optional center frequency in Hz
        
    Returns:
        Valid JSON string representation with all telemetry fields
        
    **Validates: Requirements 7.1**
    """
    try:
        # Build output dictionary with timestamp and all telemetry fields
        output = {
            "timestamp": datetime.now().isoformat(),
            "reception_time_utc": datetime.utcnow().isoformat() + "Z",
        }
        
        # Add frequency if provided
        if frequency is not None:
            output["frequency_mhz"] = frequency / 1e6
        
        # Extract all telemetry fields from the DroneID packet
        if hasattr(payload, 'droneid') and isinstance(payload.droneid, dict):
            # Include all parsed fields from the packet
            output["telemetry"] = {
                "serial_number": payload.droneid.get("serial_number", ""),
                "device_type": payload.droneid.get("device_type", "Unknown"),
                "position": {
                    "latitude": payload.droneid.get("latitude", 0.0),
                    "longitude": payload.droneid.get("longitude", 0.0),
                    "altitude_m": payload.droneid.get("altitude", 0.0),
                    "height_m": payload.droneid.get("height", 0.0),
                },
                "velocity": {
                    "north": payload.droneid.get("v_north", 0),
                    "east": payload.droneid.get("v_east", 0),
                    "up": payload.droneid.get("v_up", 0),
                },
                "home_position": {
                    "latitude": payload.droneid.get("latitude_home", 0.0),
                    "longitude": payload.droneid.get("longitude_home", 0.0),
                },
                "operator_position": {
                    "latitude": payload.droneid.get("app_lat", 0.0),
                    "longitude": payload.droneid.get("app_lon", 0.0),
                },
                "gps_time": payload.droneid.get("gps_time", 0),
                "sequence_number": payload.droneid.get("sequence_number", 0),
                "uuid": payload.droneid.get("uuid", ""),
            }
            
            # Add CRC validation status
            output["crc_valid"] = payload.check_crc()
            output["crc_packet"] = payload.droneid.get("crc-packet", "")
            output["crc_calculated"] = payload.droneid.get("crc-calculated", "")
        else:
            # Fallback: include raw payload string
            output["raw_payload"] = str(payload)
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    except Exception as e:
        # Return error JSON if formatting fails
        error_output = {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "raw_payload": str(payload) if payload else None
        }
        return json.dumps(error_output, indent=2, ensure_ascii=False)


def run_demod(samples: np.ndarray, sample_rate: float, config: ReceiverConfig, frequency: float = None,
              raw_samples_file: Path = None, verbose: bool = False) -> bool:
    """Run demodulation on received samples.
    
    Optimized with early exit when packets are found.
    
    Args:
        samples: Complex64 IQ samples
        sample_rate: Sample rate in Hz
        config: Receiver configuration
        frequency: Optional center frequency in Hz for output
        raw_samples_file: Optional path for raw samples output
        
    Returns:
        True if DroneID packet was found, False otherwise
    """
    global correct_pkt, crc_err, total_num_pkt
    
    # Optimized: smaller chunks for faster detection (250ms instead of 500ms)
    # DroneID packets are ~650μs, so 250ms is plenty
    chunk_samples = int(250e-3 * sample_rate)  # 250ms chunks
    found = False
    
    chunks = len(samples) // chunk_samples
    
    # Track packet count for this demod run to limit file size
    packets_written = 0
    max_packets_per_file = 10
    
    # Early exit: stop after finding valid packets to save processing time
    max_packets_to_process = 5  # Process at most 5 packets per capture
    packets_processed = 0
    
    for i in range(chunks):
        # Early exit if we've found enough packets
        if packets_processed >= max_packets_to_process:
            break
            
        chunk_start = i * chunk_samples
        chunk_end = (i + 1) * chunk_samples
        chunk_data = samples[chunk_start:chunk_end]
        
        capture = SC.SpectrumCapture(
            raw_data=chunk_data,
            Fs=sample_rate,
            debug=config.debug,
            p_type=config.packet_type,
            legacy=config.legacy
        )
        
        if config.debug:
            print(f"Found {len(capture.packets)} Drone-ID RF frames in spectrum capture.")
        
        total_num_pkt += len(capture.packets)
        
        # Skip empty chunks quickly
        if len(capture.packets) == 0:
            continue
        
        for packet_num, packet_raw in enumerate(capture.packets):
            # Early exit check
            if packets_processed >= max_packets_to_process:
                break
                
            # Save raw packet data - overwrite file after max packets to prevent growth
            if not config.fast and raw_samples_file is not None:
                if packets_written >= max_packets_per_file:
                    safe_write_bytes(raw_samples_file, packet_raw, append=False)
                    packets_written = 1
                else:
                    safe_write_bytes(raw_samples_file, packet_raw, append=(packets_written > 0))
                    packets_written += 1
            
            # Get packet samples with coarse CFO correction
            try:
                packet_data = capture.get_packet_samples(pktnum=packet_num, debug=config.debug)
            except ValueError as e:
                if config.debug:
                    print(f"CFO estimation failed for packet {packet_num}: {e}")
                continue
            
            try:
                packet = Packet(packet_data, debug=config.debug, legacy=config.legacy)
                if verbose or config.debug:
                    print(f"✓ Packet object created successfully")
            except Exception as e:
                if verbose or config.debug:
                    print(f"Could not decode packet: {e}")
                else:
                    print(f"Packet decode failed: {type(e).__name__}: {e}")
                continue
            
            packets_processed += 1
            
            # Get OFDM symbols
            try:
                symbols = packet.get_symbol_data(skip_zc=True)
                decoder = Decoder(symbols)
                if verbose or config.debug:
                    print(f"✓ Symbol extraction successful, {len(symbols)} symbols")
            except Exception as e:
                if verbose or config.debug:
                    print(f"Symbol extraction failed: {e}")
                else:
                    print(f"Symbol extraction failed: {type(e).__name__}")
                continue
            
            # Brute force QPSK phase alignment
            decoded_successfully = False
            for phase_corr in range(4):
                try:
                    decoder.raw_data_to_symbol_bits(phase_corr)
                    droneid_duml = decoder.magic()
                    if verbose or config.debug:
                        print(f"✓ QPSK phase {phase_corr}: decoded {len(droneid_duml) if droneid_duml else 0} bytes")
                except Exception as e:
                    if verbose or config.debug:
                        print(f"QPSK decode phase {phase_corr} failed: {e}")
                    continue
                
                if not droneid_duml:
                    if verbose or config.debug:
                        print(f"  Phase {phase_corr}: No DUML data extracted")
                    continue
                
                # Save decoded bits (skip in fast mode)
                if db_filename and not config.fast:
                    decoded_to_file(droneid_duml, db_filename)
                
                try:
                    payload = DroneIDPacket(droneid_duml)
                    if verbose or config.debug:
                        print(f"✓ DroneID packet parsed successfully")
                except Exception as e:
                    if verbose or config.debug:
                        print(f"  Phase {phase_corr}: DroneID parsing failed: {type(e).__name__}: {e}")
                    continue
                
                # Output as JSON with timestamp and frequency
                json_output = format_output_json(payload, frequency)
                print("\n" + "="*60)
                print(json_output)
                print("="*60 + "\n")
                sys.stdout.flush()  # Force output to appear immediately
                found = True
                decoded_successfully = True
                
                if not payload.check_crc():
                    crc_err += 1
                    print("⚠️  CRC validation failed")
                    continue
                
                correct_pkt += 1
                print("✅ CRC validation passed")
                break
            
            if not decoded_successfully and config.debug:
                print("Failed to decode packet with any QPSK phase")
    
    return found


def receive_thread(receiver: BladeRFReceiver, scanner: FrequencyScanner,
                   sample_queue: mp.Queue, detection_queue: mp.Queue, exit_event: threading.Event,
                   config: ReceiverConfig) -> None:
    """Thread function for receiving samples from BladeRF.
    
    Args:
        receiver: BladeRFReceiver instance
        scanner: FrequencyScanner instance
        sample_queue: Queue for passing samples to workers
        detection_queue: Queue for receiving detection notifications from workers
        exit_event: Event to signal thread termination
        config: Receiver configuration
        
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 6.1**
    """
    num_samples = scanner.calculate_num_samples()
    locked_frequency = None
    no_detection_count = 0
    max_no_detection = 10  # Resume scanning after 10 captures with no detection
    
    while not exit_event.is_set():
        # Check for detection notifications from workers
        try:
            while not detection_queue.empty():
                detected_freq = detection_queue.get_nowait()
                if detected_freq is not None and locked_frequency is None:
                    locked_frequency = detected_freq
                    no_detection_count = 0
                    print(f"\n🎯 LOCKED to {locked_frequency/1e6:.2f} MHz - continuous monitoring\n")
                elif detected_freq is not None:
                    # Reset no-detection counter on successful detection
                    no_detection_count = 0
                elif detected_freq is None and locked_frequency is not None:
                    # No detection on locked frequency
                    no_detection_count += 1
                    if no_detection_count >= max_no_detection:
                        print(f"\n📡 No detections for {max_no_detection} captures, resuming scan...\n")
                        locked_frequency = None
                        no_detection_count = 0
        except Exception:
            pass
        
        # If locked to a frequency, stay on it
        if locked_frequency is not None:
            frequency = locked_frequency
        else:
            # Get next frequency to scan
            frequency = scanner.get_next_frequency()
        
        # Set frequency on receiver
        if not receiver.set_frequency(frequency):
            print(f"Unable to set center frequency: {frequency/1e6:.2f} MHz")
            continue
        
        # Only print frequency changes when scanning (not when locked)
        if locked_frequency is None:
            if config.debug:
                print(f"Scanning: {frequency/1e6:.2f} MHz @ {config.sample_rate/1e6:.2f} MHz")
        
        try:
            # Receive samples
            samples = receiver.receive_samples(num_samples)
            
            if samples is not None and len(samples) > 0:
                # Put samples in queue for processing
                sample_queue.put((samples.copy(), frequency))
        except Exception as e:
            if config.debug:
                print(f"Error receiving samples: {e}")
            continue
    
    print("Receiver Thread: Stopped")


def process_samples(sample_rate: float, sample_queue: mp.Queue, detection_queue: mp.Queue,
                    exit_event_flag: mp.Value, config_dict: dict,
                    debug_samples_file: Path = None, raw_samples_file: Path = None) -> None:
    """Worker process function for processing samples.
    
    Args:
        sample_rate: Sample rate in Hz
        sample_queue: Queue containing samples to process
        detection_queue: Queue to signal detections back to receiver thread
        exit_event_flag: Shared value to signal process termination
        config_dict: Configuration dictionary
        debug_samples_file: Optional path for debug samples
        raw_samples_file: Optional path for raw samples
        
    **Validates: Requirements 6.2**
    """
    # Reconstruct config from dict (multiprocessing can't pickle complex objects)
    config = ReceiverConfig(
        sample_rate=config_dict['sample_rate'],
        gain=config_dict['gain'],
        duration=config_dict['duration'],
        num_workers=config_dict['num_workers'],
        debug=config_dict['debug'],
        legacy=config_dict['legacy'],
        packet_type=config_dict['packet_type'],
        fast=config_dict.get('fast', False)
    )
    
    verbose = config_dict.get('verbose', False)
    
    # Local scanner for frequency locking (each worker tracks independently)
    scanner = FrequencyScanner(duration=config.duration, sample_rate=config.sample_rate)
    
    # Track if this is the first write to debug file (for overwrite behavior)
    first_debug_write = True
    
    while True:
        try:
            # Get samples from queue with timeout
            samples, frequency = sample_queue.get(timeout=1.0)
        except Exception:
            # Check if we should exit
            if exit_event_flag.value:
                break
            continue
        
        # Check for stop signal
        if samples is None and frequency is None:
            break
        
        # Save raw samples for debugging (overwrite on first write, then skip to save disk I/O)
        if not config.fast and debug_samples_file is not None and first_debug_write:
            # Overwrite file with latest samples (not append) to prevent file growth
            safe_write_bytes(debug_samples_file, samples.tobytes(), append=False)
            first_debug_write = False
            # After first write, we skip further writes to this file to reduce I/O
        
        # Run demodulation with frequency for JSON output and session file
        found = run_demod(samples, sample_rate, config, frequency, raw_samples_file, verbose)
        
        # Signal detection back to receiver thread
        try:
            if found:
                detection_queue.put(frequency)  # Signal detection at this frequency
            else:
                detection_queue.put(None)  # Signal no detection
        except Exception:
            pass
        
        # Update scanner state
        if found:
            scanner.lock_frequency(frequency)
            if config.debug:
                print(f"Locking Frequency to {frequency/1e6:.2f} MHz")
        else:
            scanner.record_detection(False)
        
        # Check if we should exit
        if exit_event_flag.value:
            break
    
    print("Process Thread: Stopped")


def clean_up(recv_thread: threading.Thread, workers: list,
             sample_queue: mp.Queue, exit_event_flag: mp.Value) -> None:
    """Clean up threads and processes on shutdown.
    
    Args:
        recv_thread: Receiver thread
        workers: List of worker processes
        sample_queue: Sample queue
        exit_event_flag: Shared exit flag
        
    **Validates: Requirements 6.5**
    """
    print("\n\n######### Stopping Threads, please wait #########\n\n")
    
    # Wait for receiver thread to stop
    if recv_thread is not None and recv_thread.is_alive():
        recv_thread.join(timeout=10)
        if recv_thread.is_alive():
            print("Warning: Receiver thread did not stop cleanly")
    
    print("Receiver stopped")
    
    # Signal workers to stop
    exit_event_flag.value = True
    
    # Send stop signals to workers
    for worker in workers:
        if worker.is_alive():
            print(f"Send stop message to thread: {worker.name}")
            try:
                sample_queue.put((None, None), timeout=1.0)
            except Exception:
                pass
    
    # Wait for workers to finish
    for worker in workers:
        if worker.is_alive():
            worker.join(timeout=5)
            if worker.is_alive():
                print(f"Warning: Worker {worker.name} did not stop cleanly")
                worker.terminate()


def get_statistics() -> dict:
    """Get current statistics as a dictionary.
    
    Returns:
        Dictionary containing:
        - total_packets: Total packets detected
        - successful_decodes: Successfully decoded packets with valid CRC
        - crc_errors: Packets with CRC validation errors
        - success_rate: Percentage of successful decodes (or None if no packets)
        - crc_error_rate: Percentage of CRC errors among decode attempts (or None)
        
    **Validates: Requirements 7.4**
    """
    stats = {
        "total_packets": total_num_pkt,
        "successful_decodes": correct_pkt,
        "crc_errors": crc_err,
        "success_rate": None,
        "crc_error_rate": None
    }
    
    if total_num_pkt > 0:
        stats["success_rate"] = (correct_pkt / total_num_pkt) * 100
    
    decode_attempts = correct_pkt + crc_err
    if decode_attempts > 0:
        stats["crc_error_rate"] = (crc_err / decode_attempts) * 100
    
    return stats


def print_statistics() -> None:
    """Print final statistics on exit.
    
    Displays comprehensive statistics including:
    - Total packets detected
    - Successfully decoded packets
    - CRC errors
    - Success rate percentage
    
    **Validates: Requirements 7.4**
    """
    print("\n")
    print("=" * 50)
    print("         DroneID Receiver Statistics")
    print("=" * 50)
    print(f"  Total packets detected:    {total_num_pkt:>8}")
    print(f"  Successfully decoded:      {correct_pkt:>8}")
    print(f"  CRC errors:                {crc_err:>8}")
    
    # Calculate and display success rate
    if total_num_pkt > 0:
        success_rate = (correct_pkt / total_num_pkt) * 100
        print(f"  Success rate:              {success_rate:>7.1f}%")
    else:
        print(f"  Success rate:                  N/A")
    
    # Calculate decode attempts (decoded but may have CRC errors)
    decode_attempts = correct_pkt + crc_err
    if decode_attempts > 0:
        crc_error_rate = (crc_err / decode_attempts) * 100
        print(f"  CRC error rate:            {crc_error_rate:>7.1f}%")
    
    print("=" * 50)
    print()


def main():
    """Main entry point for the DroneID receiver.
    
    **Validates: Requirements 5.2, 5.4, 6.1, 6.2, 6.5**
    """
    global db_filename, receiver, args, sample_queue, detection_queue, exit_event
    global raw_samples_filename, debug_samples_filename, session_timestamp
    
    # Parse arguments
    args = parse_arguments()
    config = get_receiver_config(args)
    
    # Set up signal handlers for Windows compatibility
    setup_signal_handlers()
    
    # Create exit event and queues
    exit_event = threading.Event()
    sample_queue = mp.Queue()
    detection_queue = mp.Queue()  # For workers to signal detections
    
    # Shared flag for worker processes (mp.Event doesn't work well on Windows)
    exit_event_flag = mp.Value('b', False)
    
    # Create session timestamp for this run
    session_timestamp = datetime.now()
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        # Create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Default: current directory (src folder)
        output_dir = Path.cwd()
    
    # Generate output filenames with session timestamp (one per session)
    db_filename = output_dir / f"decoded_bits_{session_timestamp.strftime('%m%d_%H%M')}.bin"
    raw_samples_filename = output_dir / f"ext_drone_id_{int(config.sample_rate)}_{session_timestamp.strftime('%m%d_%H%M')}.raw"
    debug_samples_filename = output_dir / f"receive_test_{session_timestamp.strftime('%m%d_%H%M')}.raw"
    
    print(f"Session started at: {session_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    if args.save_files:
        print(f"Output files (rotating to prevent disk lag):")
        print(f"  Decoded bits: {db_filename}")
        print(f"  Raw samples: {raw_samples_filename} (last 10 packets)")
        print(f"  Debug samples: {debug_samples_filename} (latest capture only)")
        
        # Create empty placeholder files so user can see where they'll be saved
        create_empty_file(db_filename)
        create_empty_file(raw_samples_filename)
        create_empty_file(debug_samples_filename)
    else:
        print(f"File saving: DISABLED (use --save-files to enable)")
        print(f"Running in maximum performance mode - all output to console only")
    
    # Initialize BladeRF receiver
    print("Initializing BladeRF A4...")
    try:
        receiver = BladeRFReceiver(
            sample_rate=config.sample_rate,
            gain=config.gain
        )
    except DeviceNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except DeviceBusyError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ConfigurationError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
    
    # Create frequency scanner
    scanner = FrequencyScanner(
        receiver=receiver,
        duration=config.duration,
        sample_rate=config.sample_rate,
        band_2_4_only=getattr(args, 'band_2_4_only', False)
    )
    
    print("Start receiving...")
    
    # Start receiver thread with detection queue
    recv_thread = threading.Thread(
        target=receive_thread,
        args=(receiver, scanner, sample_queue, detection_queue, exit_event, config),
        name="ReceiverThread"
    )
    recv_thread.start()
    
    # Convert config to dict for multiprocessing
    config_dict = {
        'sample_rate': config.sample_rate,
        'gain': config.gain,
        'duration': config.duration,
        'num_workers': config.num_workers,
        'debug': config.debug,
        'legacy': config.legacy,
        'packet_type': config.packet_type,
        'fast': config.fast,
        'verbose': getattr(args, 'verbose', False)
    }
    
    # Start worker processes with session filenames and detection queue
    workers = []
    for i in range(config.num_workers):
        proc = mp.Process(
            target=process_samples,
            args=(config.sample_rate, sample_queue, detection_queue, exit_event_flag, config_dict,
                  debug_samples_filename if not config.fast else None,
                  raw_samples_filename if not config.fast else None),
            name=f"Worker-{i}"
        )
        proc.start()
        workers.append(proc)
    
    # Main loop - wait for exit signal
    try:
        while True:
            if exit_event.is_set():
                clean_up(recv_thread, workers, sample_queue, exit_event_flag)
                exit_event.clear()
                break
            
            # Check if any workers are still alive
            workers_alive = sum(1 for w in workers if w.is_alive())
            
            if workers_alive == 0:
                print("No more workers alive!\nExiting...")
                break
            
            # Small sleep to prevent busy waiting
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        # Handle Ctrl+C
        exit_event.set()
        clean_up(recv_thread, workers, sample_queue, exit_event_flag)
    finally:
        # Clean up receiver
        if receiver is not None:
            receiver.close()
    
    # Print final statistics
    print_statistics()


# Windows multiprocessing guard
if __name__ == "__main__":
    # Required for Windows multiprocessing
    mp.freeze_support()
    main()
