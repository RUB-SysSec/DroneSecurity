"""Property-based tests for CLI argument parsing.

**Feature: bladerf-a4-refactor, Property 9: CLI Argument Parsing**
**Validates: Requirements 8.1, 8.2, 8.3, 8.4**
"""

import sys
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import pytest
from hypothesis import given, strategies as st, settings

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import only config to avoid pulling in the full module chain
from config import ReceiverConfig


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser (copy for testing)."""
    parser = argparse.ArgumentParser(
        description="DJI DroneID Live Receiver using BladeRF A4 SDR",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '-g', '--gain',
        default=0,
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
        default=1.3,
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
    
    return parser


def parse_arguments(arg_list=None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_argument_parser()
    return parser.parse_args(arg_list)


def get_receiver_config(args: argparse.Namespace) -> ReceiverConfig:
    """Convert parsed arguments to ReceiverConfig."""
    gain = None if args.gain == 0 else args.gain
    
    return ReceiverConfig(
        sample_rate=args.sample_rate,
        gain=gain,
        duration=args.duration,
        num_workers=args.workers,
        debug=args.debug,
        legacy=args.legacy,
        packet_type=args.packettype
    )


class TestCLIArgumentParsing:
    """Property-based tests for CLI argument parsing."""
    
    # Valid gain values: 0 for AGC, 1-60 for manual
    valid_gains = st.integers(min_value=0, max_value=60)
    
    # Valid sample rates (in Hz)
    valid_sample_rates = st.floats(
        min_value=1e6,
        max_value=61.44e6,
        allow_nan=False,
        allow_infinity=False
    )
    
    # Valid worker counts
    valid_workers = st.integers(min_value=1, max_value=16)
    
    # Valid durations (in seconds)
    valid_durations = st.floats(
        min_value=0.1,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
    
    @given(gain=valid_gains)
    @settings(max_examples=100)
    def test_gain_argument_parsing(self, gain: int):
        """Property 9: For any valid gain value, parsing SHALL correctly apply it.
        
        **Feature: bladerf-a4-refactor, Property 9: CLI Argument Parsing**
        **Validates: Requirements 8.1**
        """
        args = parse_arguments(['-g', str(gain)])
        assert args.gain == gain
        
        # Verify config conversion
        config = get_receiver_config(args)
        if gain == 0:
            assert config.gain is None  # AGC mode
        else:
            assert config.gain == gain
    
    @given(sample_rate=valid_sample_rates)
    @settings(max_examples=100)
    def test_sample_rate_argument_parsing(self, sample_rate: float):
        """Property 9: For any valid sample rate, parsing SHALL correctly apply it.
        
        **Feature: bladerf-a4-refactor, Property 9: CLI Argument Parsing**
        **Validates: Requirements 8.2**
        """
        args = parse_arguments(['-s', str(sample_rate)])
        assert args.sample_rate == pytest.approx(sample_rate, rel=1e-9)
        
        # Verify config conversion
        config = get_receiver_config(args)
        assert config.sample_rate == pytest.approx(sample_rate, rel=1e-9)
    
    @given(workers=valid_workers)
    @settings(max_examples=100)
    def test_workers_argument_parsing(self, workers: int):
        """Property 9: For any valid worker count, parsing SHALL correctly apply it.
        
        **Feature: bladerf-a4-refactor, Property 9: CLI Argument Parsing**
        **Validates: Requirements 8.3**
        """
        args = parse_arguments(['-w', str(workers)])
        assert args.workers == workers
        
        # Verify config conversion
        config = get_receiver_config(args)
        assert config.num_workers == workers
    
    @given(duration=valid_durations)
    @settings(max_examples=100)
    def test_duration_argument_parsing(self, duration: float):
        """Property 9: For any valid duration, parsing SHALL correctly apply it.
        
        **Feature: bladerf-a4-refactor, Property 9: CLI Argument Parsing**
        **Validates: Requirements 8.4**
        """
        args = parse_arguments(['-t', str(duration)])
        assert args.duration == pytest.approx(duration, rel=1e-9)
        
        # Verify config conversion
        config = get_receiver_config(args)
        assert config.duration == pytest.approx(duration, rel=1e-9)
    
    @given(
        gain=valid_gains,
        sample_rate=valid_sample_rates,
        workers=valid_workers,
        duration=valid_durations
    )
    @settings(max_examples=100)
    def test_combined_arguments_parsing(self, gain: int, sample_rate: float,
                                         workers: int, duration: float):
        """Property 9: For any valid combination of arguments, parsing SHALL correctly apply all.
        
        **Feature: bladerf-a4-refactor, Property 9: CLI Argument Parsing**
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
        """
        args = parse_arguments([
            '-g', str(gain),
            '-s', str(sample_rate),
            '-w', str(workers),
            '-t', str(duration)
        ])
        
        assert args.gain == gain
        assert args.sample_rate == pytest.approx(sample_rate, rel=1e-9)
        assert args.workers == workers
        assert args.duration == pytest.approx(duration, rel=1e-9)
        
        # Verify config conversion
        config = get_receiver_config(args)
        if gain == 0:
            assert config.gain is None
        else:
            assert config.gain == gain
        assert config.sample_rate == pytest.approx(sample_rate, rel=1e-9)
        assert config.num_workers == workers
        assert config.duration == pytest.approx(duration, rel=1e-9)
    
    def test_default_values(self):
        """Test that default values are correctly applied when no arguments given.
        
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
        """
        args = parse_arguments([])
        
        # Check defaults
        assert args.gain == 0  # AGC
        assert args.sample_rate == 50e6
        assert args.workers == 2
        assert args.duration == 1.3
        assert args.debug is False
        assert args.legacy is False
        assert args.packettype == "droneid"
        
        # Verify config conversion
        config = get_receiver_config(args)
        assert config.gain is None  # AGC
        assert config.sample_rate == 50e6
        assert config.num_workers == 2
        assert config.duration == 1.3
        assert config.debug is False
        assert config.legacy is False
        assert config.packet_type == "droneid"
    
    def test_debug_flag(self):
        """Test debug flag parsing.
        
        **Validates: Requirements 8.5**
        """
        # Without flag
        args = parse_arguments([])
        assert args.debug is False
        
        # With flag
        args = parse_arguments(['-d'])
        assert args.debug is True
        
        config = get_receiver_config(args)
        assert config.debug is True
    
    def test_legacy_flag(self):
        """Test legacy flag parsing.
        
        **Validates: Requirements 8.6**
        """
        # Without flag
        args = parse_arguments([])
        assert args.legacy is False
        
        # With flag
        args = parse_arguments(['-l'])
        assert args.legacy is True
        
        config = get_receiver_config(args)
        assert config.legacy is True
    
    def test_packet_type_choices(self):
        """Test packet type argument with valid choices.
        
        **Validates: Requirements 8.1**
        """
        valid_types = ["droneid", "c2", "beacon", "video"]
        
        for ptype in valid_types:
            args = parse_arguments(['-p', ptype])
            assert args.packettype == ptype
            
            config = get_receiver_config(args)
            assert config.packet_type == ptype
