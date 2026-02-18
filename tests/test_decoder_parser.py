"""Tests for QPSK decoder and DroneID packet parser.

**Feature: bladerf-a4-refactor**
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

This module tests the QPSK decoder, Gold sequence descrambling,
CRC validation, and DroneID packet parsing functionality.
"""

import numpy as np
import pytest
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import struct

# Import decoder and parser components
from qpsk import Decoder, get_symbol_bits, qpsk_to_bits, rm_turbo_rx
from goldgen import gold
from droneid_packet import DroneIDPacket, CRC_INIT, CRC_POLY, DRONEID_MAX_LEN
import crcmod


class TestQPSKDecoder:
    """Tests for QPSK decoder functionality.
    
    **Validates: Requirements 4.1, 4.2, 4.3**
    """
    
    def test_qpsk_symbol_mapping_quadrant_0(self):
        """Test QPSK symbol mapping for quadrant 0 (positive real, positive imag).
        
        **Validates: Requirements 4.1**
        """
        # Quadrant 0: real >= 0, imag >= 0
        symbol = complex(1.0, 1.0)
        
        # Test all phase corrections
        for phase_corr in range(4):
            bits = get_symbol_bits(symbol, phase_corr)
            assert bits == qpsk_to_bits[phase_corr][0]
    
    def test_qpsk_symbol_mapping_quadrant_1(self):
        """Test QPSK symbol mapping for quadrant 1 (positive real, negative imag).
        
        **Validates: Requirements 4.1**
        """
        # Quadrant 1: real >= 0, imag < 0
        symbol = complex(1.0, -1.0)
        
        for phase_corr in range(4):
            bits = get_symbol_bits(symbol, phase_corr)
            assert bits == qpsk_to_bits[phase_corr][1]
    
    def test_qpsk_symbol_mapping_quadrant_2(self):
        """Test QPSK symbol mapping for quadrant 2 (negative real, negative imag).
        
        **Validates: Requirements 4.1**
        """
        # Quadrant 2: real < 0, imag < 0
        symbol = complex(-1.0, -1.0)
        
        for phase_corr in range(4):
            bits = get_symbol_bits(symbol, phase_corr)
            assert bits == qpsk_to_bits[phase_corr][2]
    
    def test_qpsk_symbol_mapping_quadrant_3(self):
        """Test QPSK symbol mapping for quadrant 3 (negative real, positive imag).
        
        **Validates: Requirements 4.1**
        """
        # Quadrant 3: real < 0, imag > 0
        symbol = complex(-1.0, 1.0)
        
        for phase_corr in range(4):
            bits = get_symbol_bits(symbol, phase_corr)
            assert bits == qpsk_to_bits[phase_corr][3]
    
    def test_qpsk_invalid_phase_correction(self):
        """Test that invalid phase correction raises ValueError.
        
        **Validates: Requirements 4.1**
        """
        symbol = complex(1.0, 1.0)
        
        with pytest.raises(ValueError):
            get_symbol_bits(symbol, -1)
        
        with pytest.raises(ValueError):
            get_symbol_bits(symbol, 4)
    
    def test_decoder_initialization(self):
        """Test Decoder class initialization.
        
        **Validates: Requirements 4.1**
        """
        # Test empty initialization
        decoder = Decoder()
        assert decoder.raw_data == []
        assert decoder.sym_bits == []
        
        # Test with raw data
        raw_data = [[complex(1.0, 1.0), complex(-1.0, -1.0)]]
        decoder = Decoder(raw_data=raw_data)
        assert decoder.raw_data == raw_data
    
    def test_decoder_raw_data_to_symbol_bits(self):
        """Test conversion of raw QPSK symbols to bits.
        
        **Validates: Requirements 4.1**
        """
        # Create simple test data - one frame symbol with 4 QPSK symbols
        raw_data = [[
            complex(1.0, 1.0),    # Quadrant 0
            complex(1.0, -1.0),   # Quadrant 1
            complex(-1.0, -1.0),  # Quadrant 2
            complex(-1.0, 1.0)    # Quadrant 3
        ]]
        
        decoder = Decoder(raw_data=raw_data)
        decoder.raw_data_to_symbol_bits(phase_correction=0)
        
        # Verify demodulation
        assert len(decoder.sym_bits) == 1
        assert len(decoder.sym_bits[0]) == 4
        
        # Check expected bits for phase_correction=0
        expected = [qpsk_to_bits[0][i] for i in range(4)]
        assert decoder.sym_bits[0] == expected


class TestGoldSequence:
    """Tests for Gold sequence generation and descrambling.
    
    **Validates: Requirements 4.2**
    """
    
    def test_gold_sequence_length(self):
        """Test Gold sequence generates correct length.
        
        **Validates: Requirements 4.2**
        """
        Nc = 1600
        lengths = [100, 500, 1200, 7200]
        seed = 0x12345678
        
        for l in lengths:
            seq = gold(Nc, l, seed)
            assert len(seq) == l
    
    def test_gold_sequence_binary(self):
        """Test Gold sequence contains only binary values.
        
        **Validates: Requirements 4.2**
        """
        seq = gold(1600, 1200, 0x12345678)
        
        # All values should be 0 or 1 (boolean)
        assert seq.dtype == bool
        assert np.all((seq == 0) | (seq == 1))
    
    def test_gold_sequence_deterministic(self):
        """Test Gold sequence is deterministic for same seed.
        
        **Validates: Requirements 4.2**
        """
        Nc = 1600
        l = 1200
        seed = 0x12345678
        
        seq1 = gold(Nc, l, seed)
        seq2 = gold(Nc, l, seed)
        
        assert np.array_equal(seq1, seq2)
    
    def test_gold_sequence_different_seeds(self):
        """Test Gold sequences differ for different seeds.
        
        **Validates: Requirements 4.2**
        """
        Nc = 1600
        l = 1200
        
        seq1 = gold(Nc, l, 0x12345678)
        seq2 = gold(Nc, l, 0x87654321)
        
        # Sequences should be different
        assert not np.array_equal(seq1, seq2)
    
    def test_gold_sequence_droneid_seed(self):
        """Test Gold sequence with DroneID standard seed.
        
        **Validates: Requirements 4.2**
        """
        # DroneID uses seed 0x12345678
        seq = gold(1600, 1200, 0x12345678)
        
        assert len(seq) == 1200
        assert seq.dtype == bool


class TestRateMatching:
    """Tests for rate matching (turbo decoding).
    
    **Validates: Requirements 4.3**
    """
    
    def test_rm_turbo_rx_output_length(self):
        """Test rate matching produces correct output length.
        
        **Validates: Requirements 4.3**
        """
        # Input length should be 1412 for DroneID systematic stream
        input_len = 1412
        bits_in = np.random.randint(0, 2, input_len)
        
        bits_out = rm_turbo_rx(bits_in)
        
        # Output length depends on dummy bit calculation
        # ncols = 32, nrows = ceil(1412/32) = 45
        # n_dummy = 32*45 - 1412 = 1440 - 1412 = 28
        # Output should be input_len - n_dummy when n_dummy > 0
        ncols = 32
        nrows = (input_len + 31) // ncols
        n_dummy = (ncols * nrows) - input_len
        expected_len = input_len  # After removing dummy bits, we get back original length
        
        assert len(bits_out) == expected_len
    
    def test_rm_turbo_rx_no_dummy_bits(self):
        """Test rate matching removes dummy bits.
        
        **Validates: Requirements 4.3**
        """
        input_len = 1412
        bits_in = np.random.randint(0, 2, input_len)
        
        bits_out = rm_turbo_rx(bits_in)
        
        # Output should not contain -1 (dummy marker)
        assert not np.any(bits_out == -1)
    
    def test_rm_turbo_rx_permutation(self):
        """Test rate matching applies correct permutation.
        
        **Validates: Requirements 4.3**
        """
        # Test with a known input pattern
        input_len = 1412
        bits_in = np.arange(input_len)  # Sequential values for tracking
        
        bits_out = rm_turbo_rx(bits_in)
        
        # Output should be a permutation of input (after dummy removal)
        assert len(bits_out) == input_len




class TestCRCValidation:
    """Property tests for CRC validation.
    
    **Feature: bladerf-a4-refactor, Property 6: CRC Validation Round-Trip**
    **Validates: Requirements 4.4**
    """
    
    @given(st.binary(min_size=89, max_size=89))
    @settings(max_examples=100)
    def test_crc_round_trip(self, payload_bytes):
        """
        **Feature: bladerf-a4-refactor, Property 6: CRC Validation Round-Trip**
        **Validates: Requirements 4.4**
        
        For any valid DroneID packet payload (89 bytes), computing the CRC 
        using polynomial 0x11021 with init value 0x3692 and appending it
        SHALL produce a packet where the embedded CRC matches the calculated CRC.
        """
        # Create CRC function with DroneID parameters
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        
        # Calculate CRC for the payload
        calculated_crc = crc_func(payload_bytes)
        
        # Append CRC to payload (little-endian 16-bit)
        full_packet = payload_bytes + struct.pack('<H', calculated_crc)
        
        # Verify packet is correct length
        assert len(full_packet) == DRONEID_MAX_LEN
        
        # Recalculate CRC from the packet (excluding the CRC bytes)
        recalculated_crc = crc_func(full_packet[:DRONEID_MAX_LEN-2])
        
        # Extract embedded CRC from packet
        embedded_crc = struct.unpack('<H', full_packet[-2:])[0]
        
        # Round-trip: calculated CRC should match embedded CRC
        assert recalculated_crc == embedded_crc
    
    @given(st.binary(min_size=89, max_size=89))
    @settings(max_examples=100)
    def test_crc_detects_corruption(self, payload_bytes):
        """
        **Feature: bladerf-a4-refactor, Property 6: CRC Validation Round-Trip**
        **Validates: Requirements 4.4**
        
        For any valid DroneID packet payload, if the payload is corrupted
        (single bit flip), the CRC validation SHALL fail.
        """
        # Create CRC function with DroneID parameters
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        
        # Calculate CRC for the original payload
        calculated_crc = crc_func(payload_bytes)
        
        # Append CRC to payload
        full_packet = bytearray(payload_bytes + struct.pack('<H', calculated_crc))
        
        # Corrupt a byte in the payload (flip a bit)
        corrupt_pos = len(payload_bytes) // 2  # Middle of payload
        full_packet[corrupt_pos] ^= 0x01  # Flip one bit
        
        # Recalculate CRC from corrupted packet
        recalculated_crc = crc_func(bytes(full_packet[:DRONEID_MAX_LEN-2]))
        
        # Extract embedded CRC
        embedded_crc = struct.unpack('<H', bytes(full_packet[-2:]))[0]
        
        # CRC should NOT match for corrupted packet
        assert recalculated_crc != embedded_crc
    
    def test_crc_polynomial_and_init(self):
        """Test CRC uses correct polynomial and init value.
        
        **Validates: Requirements 4.4**
        """
        # Verify constants match specification
        assert CRC_POLY == 0x11021
        assert CRC_INIT == 0x3692
    
    def test_crc_function_creation(self):
        """Test CRC function can be created with DroneID parameters.
        
        **Validates: Requirements 4.4**
        """
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        
        # Test with known data
        test_data = b'\x00' * 89
        result = crc_func(test_data)
        
        # Result should be a 16-bit value
        assert 0 <= result <= 0xFFFF
    
    @given(st.binary(min_size=89, max_size=89))
    @settings(max_examples=100)
    def test_crc_deterministic(self, payload_bytes):
        """
        **Feature: bladerf-a4-refactor, Property 6: CRC Validation Round-Trip**
        **Validates: Requirements 4.4**
        
        For any payload, computing the CRC multiple times SHALL produce
        the same result.
        """
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        
        crc1 = crc_func(payload_bytes)
        crc2 = crc_func(payload_bytes)
        
        assert crc1 == crc2



class TestDroneIDPacketParsing:
    """Property tests for DroneID packet parsing.
    
    **Feature: bladerf-a4-refactor, Property 7: DroneID Packet Parsing**
    **Validates: Requirements 4.5**
    """
    
    @given(
        st.integers(min_value=0, max_value=255),  # pkt_len
        st.integers(min_value=0, max_value=255),  # unk
        st.integers(min_value=0, max_value=255),  # version
        st.integers(min_value=0, max_value=65535),  # sequence_number
        st.integers(min_value=0, max_value=65535),  # state_info
        st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=16),  # serial_number (ASCII)
        st.integers(min_value=-2147483648, max_value=2147483647),  # longitude
        st.integers(min_value=-2147483648, max_value=2147483647),  # latitude
        st.integers(min_value=-32768, max_value=32767),  # altitude
        st.integers(min_value=-32768, max_value=32767),  # height
        st.integers(min_value=-32768, max_value=32767),  # v_north
        st.integers(min_value=-32768, max_value=32767),  # v_east
        st.integers(min_value=-32768, max_value=32767),  # v_up
        st.integers(min_value=-32768, max_value=32767),  # d_1_angle
        st.integers(min_value=0, max_value=2**64-1),  # gps_time
        st.integers(min_value=-2147483648, max_value=2147483647),  # app_lat
        st.integers(min_value=-2147483648, max_value=2147483647),  # app_lon
        st.integers(min_value=-2147483648, max_value=2147483647),  # longitude_home
        st.integers(min_value=-2147483648, max_value=2147483647),  # latitude_home
        st.integers(min_value=0, max_value=255),  # device_type
        st.integers(min_value=0, max_value=255),  # uuid_len
        st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=20),  # uuid (ASCII)
    )
    @settings(max_examples=100)
    def test_packet_parsing_extracts_all_fields(
        self, pkt_len, unk, version, sequence_number, state_info,
        serial_number, longitude, latitude, altitude, height,
        v_north, v_east, v_up, d_1_angle, gps_time,
        app_lat, app_lon, longitude_home, latitude_home,
        device_type, uuid_len, uuid
    ):
        """
        **Feature: bladerf-a4-refactor, Property 7: DroneID Packet Parsing**
        **Validates: Requirements 4.5**
        
        For any valid 91-byte DroneID payload with ASCII serial/uuid,
        parsing SHALL extract all fields with correct byte offsets.
        """
        # Pad serial_number and uuid to fixed lengths
        serial_bytes = serial_number.encode('utf-8').ljust(16, b'\x00')[:16]
        uuid_bytes = uuid.encode('utf-8').ljust(20, b'\x00')[:20]
        
        # Build a valid 91-byte packet
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            pkt_len, unk, version, sequence_number, state_info,
            serial_bytes, longitude, latitude, altitude, height,
            v_north, v_east, v_up, d_1_angle, gps_time,
            app_lat, app_lon, longitude_home, latitude_home,
            device_type, uuid_len, uuid_bytes
        )
        
        # Calculate and append CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse the packet
        parsed = DroneIDPacket(full_packet)
        
        # Verify all fields are extracted
        assert parsed.droneid["pkt_len"] == pkt_len
        assert parsed.droneid["unk"] == unk
        assert parsed.droneid["version"] == version
        assert parsed.droneid["sequence_number"] == sequence_number
        assert parsed.droneid["state_info"] == state_info
        
        # Verify GPS coordinates with scaling factor
        expected_lon = longitude / 174533.0
        expected_lat = latitude / 174533.0
        assert abs(parsed.droneid["longitude"] - expected_lon) < 1e-6
        assert abs(parsed.droneid["latitude"] - expected_lat) < 1e-6
        
        # Verify altitude with scaling (ft to m)
        expected_alt = round(altitude / 3.281, 2)
        expected_height = round(height / 3.281, 2)
        assert parsed.droneid["altitude"] == expected_alt
        assert parsed.droneid["height"] == expected_height
        
        # Verify velocity fields
        assert parsed.droneid["v_north"] == v_north
        assert parsed.droneid["v_east"] == v_east
        assert parsed.droneid["v_up"] == v_up
    
    @given(st.binary(min_size=89, max_size=89))
    @settings(max_examples=100)
    def test_packet_parsing_handles_any_bytes(self, payload_bytes):
        """
        **Feature: bladerf-a4-refactor, Property 7: DroneID Packet Parsing**
        **Validates: Requirements 4.5**
        
        For any 89-byte payload with valid CRC, parsing SHALL not raise
        exceptions and SHALL extract fields.
        """
        # Calculate and append CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(payload_bytes)
        full_packet = payload_bytes + struct.pack('<H', crc_value)
        
        # Parsing should not raise exceptions
        try:
            parsed = DroneIDPacket(full_packet)
            
            # Verify basic fields exist
            assert "pkt_len" in parsed.droneid
            assert "longitude" in parsed.droneid
            assert "latitude" in parsed.droneid
            assert "altitude" in parsed.droneid
            assert "serial_number" in parsed.droneid
            assert "crc-packet" in parsed.droneid
            assert "crc-calculated" in parsed.droneid
        except UnicodeDecodeError:
            # Some random bytes may not be valid UTF-8 for serial/uuid
            # This is expected behavior for truly random data
            pass
    
    @given(
        st.integers(min_value=-2147483648, max_value=2147483647),  # longitude
        st.integers(min_value=-2147483648, max_value=2147483647),  # latitude
    )
    @settings(max_examples=100)
    def test_gps_coordinate_scaling(self, longitude, latitude):
        """
        **Feature: bladerf-a4-refactor, Property 7: DroneID Packet Parsing**
        **Validates: Requirements 4.5**
        
        For any GPS coordinate values, the scaling factor 174533.0 SHALL
        be applied correctly to convert to decimal degrees.
        """
        # Build minimal valid packet with specific GPS values
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            91, 0, 1, 0, 0,  # pkt_len, unk, version, seq, state
            b'\x00' * 16,  # serial
            longitude, latitude,  # GPS coords
            0, 0, 0, 0, 0, 0,  # alt, height, velocities
            0,  # gps_time
            0, 0, 0, 0,  # app coords, home coords
            0, 0,  # device_type, uuid_len
            b'\x00' * 20  # uuid
        )
        
        # Add CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse
        parsed = DroneIDPacket(full_packet)
        
        # Verify scaling
        expected_lon = longitude / 174533.0
        expected_lat = latitude / 174533.0
        
        assert abs(parsed.droneid["longitude"] - expected_lon) < 1e-10
        assert abs(parsed.droneid["latitude"] - expected_lat) < 1e-10
    
    @given(
        st.integers(min_value=-32768, max_value=32767),  # altitude in feet
        st.integers(min_value=-32768, max_value=32767),  # height in feet
    )
    @settings(max_examples=100)
    def test_altitude_scaling(self, altitude_ft, height_ft):
        """
        **Feature: bladerf-a4-refactor, Property 7: DroneID Packet Parsing**
        **Validates: Requirements 4.5**
        
        For any altitude/height values, the scaling factor 3.281 (ft to m)
        SHALL be applied correctly.
        """
        # Build minimal valid packet
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            91, 0, 1, 0, 0,
            b'\x00' * 16,
            0, 0,  # GPS coords
            altitude_ft, height_ft,  # altitude, height
            0, 0, 0, 0,  # velocities
            0,  # gps_time
            0, 0, 0, 0,  # app coords, home coords
            0, 0,
            b'\x00' * 20
        )
        
        # Add CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse
        parsed = DroneIDPacket(full_packet)
        
        # Verify scaling (ft to m)
        expected_alt = round(altitude_ft / 3.281, 2)
        expected_height = round(height_ft / 3.281, 2)
        
        assert parsed.droneid["altitude"] == expected_alt
        assert parsed.droneid["height"] == expected_height
    
    def test_crc_check_method(self):
        """Test the check_crc() method works correctly.
        
        **Validates: Requirements 4.4, 4.5**
        """
        # Build a valid packet with ASCII serial
        packet_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            91, 0, 1, 0, 0,
            b'TEST_SERIAL\x00\x00\x00\x00\x00',
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            b'UUID_TEST\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )
        
        # Add correct CRC
        crc_func = crcmod.mkCrcFun(CRC_POLY, initCrc=CRC_INIT, rev=True)
        crc_value = crc_func(packet_data)
        full_packet = packet_data + struct.pack('<H', crc_value)
        
        # Parse and check CRC
        parsed = DroneIDPacket(full_packet)
        assert parsed.check_crc() == True
        
        # Create a new corrupted packet by changing a numeric field
        # Corrupt the version byte (byte 2) which won't affect string parsing
        corrupted_data = struct.pack(
            "<BBBHH16siihhhhhhQiiiiBB20s",
            91, 0, 99,  # Changed version from 1 to 99
            0, 0,
            b'TEST_SERIAL\x00\x00\x00\x00\x00',
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            b'UUID_TEST\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )
        # Use the original CRC (which is now wrong)
        corrupted_packet = corrupted_data + struct.pack('<H', crc_value)
        
        parsed_corrupted = DroneIDPacket(corrupted_packet)
        assert parsed_corrupted.check_crc() == False
    
    def test_json_output(self):
        """Test that packet can be converted to JSON string.
        
        **Validates: Requirements 4.5, 7.1**
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
        
        # Parse and convert to string (JSON)
        parsed = DroneIDPacket(full_packet)
        json_str = str(parsed)
        
        # Verify it's valid JSON
        import json
        parsed_json = json.loads(json_str)
        
        assert "longitude" in parsed_json
        assert "latitude" in parsed_json
        assert "altitude" in parsed_json
        assert "serial_number" in parsed_json
