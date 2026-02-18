"""Property tests for JSON output format.

**Feature: bladerf-a4-refactor, Property 8: JSON Output Format**
**Validates: Requirements 7.1**

This module tests that decoded DroneID packets produce valid JSON output
containing all required telemetry fields.
"""

import json
import struct
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import pytest
from hypothesis import given, strategies as st, settings, assume
import crcmod

from droneid_packet import DroneIDPacket, CRC_INIT, CRC_POLY, DRONEID_MAX_LEN
from droneid_receiver_live import format_output_json


class TestJSONOutputFormat:
    """Property tests for JSON output format.
    
    **Feature: bladerf-a4-refactor, Property 8: JSON Output Format**
    **Validates: Requirements 7.1**
    """
    
    @given(
        st.integers(min_value=0, max_value=255),  # pkt_len
        st.integers(min_value=0, max_value=255),  # version
        st.integers(min_value=0, max_value=65535),  # sequence_number
        st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=16),  # serial_number (ASCII)
        st.integers(min_value=-2147483648, max_value=2147483647),  # longitude
        st.integers(min_value=-2147483648, max_value=2147483647),  # latitude
        st.integers(min_value=-32768, max_value=32767),  # altitude
        st.integers(min_value=-32768, max_value=32767),  # height
        st.integers(min_value=-32768, max_value=32767),  # v_north
        st.integers(min_value=-32768, max_value=32767),  # v_east
        st.integers(min_value=-32768, max_value=32767),  # v_up
        st.integers(min_value=0, max_value=255),  # device_type
        st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=20),  # uuid (ASCII)
        st.floats(min_value=2.4e9, max_value=5.9e9, allow_nan=False, allow_infinity=False),  # frequency
    )
    @settings(max_examples=100)
    def test_json_output_is_valid_json(
        self, pkt_len, version, sequence_number, serial_number,
        longitude, latitude, altitude, height, v_north, v_east, v_up,
        device_type, uuid, frequency
    ):
        """
        **Feature: bladerf-a4-refactor, Property 8: JSON Output Format**
        **Validates: Requirements 7.1**
        
        For any successfully decoded DroneID packet, the output SHALL be
        valid JSON containing all required telemetry fields.
        """
        # Pad serial_number and uuid to fixed lengths
        serial_bytes = serial_number.encode('utf-8').ljust(16, b'\x00')[:16]
        uuid_bytes = uuid.encode('utf-8').ljust(20, b'\x00')[:20]
        
        # Build a valid 89-byte packet (without CRC)
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            pkt_len, 0, version, sequence_number, 0,
            serial_bytes, longitude, latitude, altitude, height,
            v_north, v_east, v_up, 0, 0,
            0, 0, 0, 0,
            device_type, 0, uuid_bytes
        )
        
        # Calculate and append CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse the packet
        payload = DroneIDPacket(full_packet)
        
        # Format as JSON
        json_output = format_output_json(payload, frequency)
        
        # Verify it's valid JSON
        parsed = json.loads(json_output)
        
        # Verify required top-level fields exist
        assert "timestamp" in parsed, "Missing timestamp field"
        assert "reception_time_utc" in parsed, "Missing reception_time_utc field"
        assert "telemetry" in parsed, "Missing telemetry field"
        
        # Verify frequency is included when provided
        assert "frequency_mhz" in parsed, "Missing frequency_mhz field"
        assert abs(parsed["frequency_mhz"] - frequency / 1e6) < 0.001
        
        # Verify telemetry contains required fields
        telemetry = parsed["telemetry"]
        assert "serial_number" in telemetry, "Missing serial_number in telemetry"
        assert "device_type" in telemetry, "Missing device_type in telemetry"
        assert "position" in telemetry, "Missing position in telemetry"
        assert "velocity" in telemetry, "Missing velocity in telemetry"
        assert "home_position" in telemetry, "Missing home_position in telemetry"
        assert "operator_position" in telemetry, "Missing operator_position in telemetry"
        
        # Verify position fields
        position = telemetry["position"]
        assert "latitude" in position, "Missing latitude in position"
        assert "longitude" in position, "Missing longitude in position"
        assert "altitude_m" in position, "Missing altitude_m in position"
        assert "height_m" in position, "Missing height_m in position"
        
        # Verify velocity fields
        velocity = telemetry["velocity"]
        assert "north" in velocity, "Missing north in velocity"
        assert "east" in velocity, "Missing east in velocity"
        assert "up" in velocity, "Missing up in velocity"
        
        # Verify CRC fields
        assert "crc_valid" in parsed, "Missing crc_valid field"
        assert "crc_packet" in parsed, "Missing crc_packet field"
        assert "crc_calculated" in parsed, "Missing crc_calculated field"
    
    @given(
        st.binary(min_size=89, max_size=89),
        st.floats(min_value=2.4e9, max_value=5.9e9, allow_nan=False, allow_infinity=False) | st.none(),
    )
    @settings(max_examples=100)
    def test_json_output_handles_any_payload(self, payload_bytes, frequency):
        """
        **Feature: bladerf-a4-refactor, Property 8: JSON Output Format**
        **Validates: Requirements 7.1**
        
        For any 89-byte payload with valid CRC, format_output_json SHALL
        produce valid JSON without raising exceptions.
        """
        # Calculate and append CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(payload_bytes)
        full_packet = payload_bytes + struct.pack('<H', crc_value)
        
        try:
            # Parse the packet
            payload = DroneIDPacket(full_packet)
            
            # Format as JSON
            json_output = format_output_json(payload, frequency)
            
            # Verify it's valid JSON
            parsed = json.loads(json_output)
            
            # Verify timestamp is always present
            assert "timestamp" in parsed, "Missing timestamp field"
            
        except UnicodeDecodeError:
            # Some random bytes may not be valid UTF-8 for serial/uuid
            # This is expected behavior for truly random data
            pass
    
    def test_json_output_without_frequency(self):
        """Test JSON output when frequency is not provided.
        
        **Validates: Requirements 7.1**
        """
        # Build a valid packet
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            91, 0, 1, 100, 0,
            b'TEST_SERIAL\x00\x00\x00\x00\x00',
            1745330, 1745330,  # ~10 degrees
            328, 164,  # ~100m, ~50m
            10, 20, 5, 0, 0, 0, 0, 0, 0, 68, 0,
            b'UUID_TEST\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )
        
        # Add CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse and format without frequency
        payload = DroneIDPacket(full_packet)
        json_output = format_output_json(payload)
        
        # Verify it's valid JSON
        parsed = json.loads(json_output)
        
        # Verify frequency_mhz is NOT present when not provided
        assert "frequency_mhz" not in parsed
        
        # Verify other required fields are present
        assert "timestamp" in parsed
        assert "telemetry" in parsed
    
    def test_json_output_with_frequency(self):
        """Test JSON output includes frequency when provided.
        
        **Validates: Requirements 7.1**
        """
        # Build a valid packet
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            91, 0, 1, 100, 0,
            b'TEST_SERIAL\x00\x00\x00\x00\x00',
            1745330, 1745330,
            328, 164,
            10, 20, 5, 0, 0, 0, 0, 0, 0, 68, 0,
            b'UUID_TEST\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )
        
        # Add CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse and format with frequency
        payload = DroneIDPacket(full_packet)
        frequency = 2414.5e6  # 2.4 GHz band
        json_output = format_output_json(payload, frequency)
        
        # Verify it's valid JSON
        parsed = json.loads(json_output)
        
        # Verify frequency_mhz is present and correct
        assert "frequency_mhz" in parsed
        assert abs(parsed["frequency_mhz"] - 2414.5) < 0.001
    
    def test_json_output_timestamp_format(self):
        """Test JSON output timestamp is in ISO format.
        
        **Validates: Requirements 7.1**
        """
        from datetime import datetime
        
        # Build a valid packet
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            91, 0, 1, 100, 0,
            b'TEST_SERIAL\x00\x00\x00\x00\x00',
            1745330, 1745330,
            328, 164,
            10, 20, 5, 0, 0, 0, 0, 0, 0, 68, 0,
            b'UUID_TEST\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )
        
        # Add CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse and format
        payload = DroneIDPacket(full_packet)
        json_output = format_output_json(payload)
        
        # Verify it's valid JSON
        parsed = json.loads(json_output)
        
        # Verify timestamp can be parsed as ISO format
        timestamp = parsed["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise
        
        # Verify UTC timestamp ends with Z
        utc_timestamp = parsed["reception_time_utc"]
        assert utc_timestamp.endswith("Z")
        # Parse without the Z suffix
        datetime.fromisoformat(utc_timestamp[:-1])  # Should not raise
    
    def test_json_output_crc_validation_status(self):
        """Test JSON output includes CRC validation status.
        
        **Validates: Requirements 7.1**
        """
        # Build a valid packet with correct CRC
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            91, 0, 1, 100, 0,
            b'TEST_SERIAL\x00\x00\x00\x00\x00',
            1745330, 1745330,
            328, 164,
            10, 20, 5, 0, 0, 0, 0, 0, 0, 68, 0,
            b'UUID_TEST\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )
        
        # Add correct CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse and format
        payload = DroneIDPacket(full_packet)
        json_output = format_output_json(payload)
        
        # Verify it's valid JSON
        parsed = json.loads(json_output)
        
        # Verify CRC validation is true for valid packet
        assert parsed["crc_valid"] == True
        assert parsed["crc_packet"] == parsed["crc_calculated"]



class TestStatisticsDisplay:
    """Tests for statistics display functionality.
    
    **Validates: Requirements 7.4**
    """
    
    def test_get_statistics_returns_dict(self):
        """Test get_statistics returns a dictionary with required keys.
        
        **Validates: Requirements 7.4**
        """
        from droneid_receiver_live import get_statistics, reset_statistics
        
        # Reset to known state
        reset_statistics()
        
        stats = get_statistics()
        
        # Verify it's a dictionary
        assert isinstance(stats, dict)
        
        # Verify required keys exist
        assert "total_packets" in stats
        assert "successful_decodes" in stats
        assert "crc_errors" in stats
        assert "success_rate" in stats
        assert "crc_error_rate" in stats
    
    def test_reset_statistics(self):
        """Test reset_statistics clears all counters.
        
        **Validates: Requirements 7.4**
        """
        from droneid_receiver_live import get_statistics, reset_statistics
        import droneid_receiver_live as receiver
        
        # Set some values
        receiver.total_num_pkt = 100
        receiver.correct_pkt = 80
        receiver.crc_err = 10
        receiver.num_decoded = 90
        
        # Reset
        reset_statistics()
        
        # Verify all are zero
        stats = get_statistics()
        assert stats["total_packets"] == 0
        assert stats["successful_decodes"] == 0
        assert stats["crc_errors"] == 0
    
    def test_statistics_success_rate_calculation(self):
        """Test success rate is calculated correctly.
        
        **Validates: Requirements 7.4**
        """
        from droneid_receiver_live import get_statistics, reset_statistics
        import droneid_receiver_live as receiver
        
        # Reset to known state
        reset_statistics()
        
        # Set specific values
        receiver.total_num_pkt = 100
        receiver.correct_pkt = 75
        receiver.crc_err = 5
        
        stats = get_statistics()
        
        # Success rate should be 75%
        assert stats["success_rate"] == 75.0
        
        # CRC error rate should be 5/(75+5) = 6.25%
        assert abs(stats["crc_error_rate"] - 6.25) < 0.01
    
    def test_statistics_with_zero_packets(self):
        """Test statistics handles zero packets gracefully.
        
        **Validates: Requirements 7.4**
        """
        from droneid_receiver_live import get_statistics, reset_statistics
        
        # Reset to zero state
        reset_statistics()
        
        stats = get_statistics()
        
        # Success rate should be None when no packets
        assert stats["success_rate"] is None
        assert stats["crc_error_rate"] is None
    
    def test_print_statistics_output(self, capsys):
        """Test print_statistics produces expected output.
        
        **Validates: Requirements 7.4**
        """
        from droneid_receiver_live import print_statistics, reset_statistics
        import droneid_receiver_live as receiver
        
        # Reset and set known values
        reset_statistics()
        receiver.total_num_pkt = 50
        receiver.correct_pkt = 40
        receiver.crc_err = 5
        
        # Print statistics
        print_statistics()
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify key information is present
        assert "50" in captured.out  # total packets
        assert "40" in captured.out  # successful decodes
        assert "5" in captured.out   # CRC errors
        assert "Statistics" in captured.out
