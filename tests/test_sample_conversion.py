"""Property-based tests for SC16_Q11 to complex64 sample format conversion.

**Feature: bladerf-a4-refactor, Property 1: Sample Format Conversion**
**Validates: Requirements 1.5**

This module tests that SC16_Q11 formatted samples (16-bit signed integers 
representing I and Q) are correctly converted to complex64 format with 
values in the range [-1.0, 1.0] and correct I/Q pairing.
"""

import numpy as np
from hypothesis import given, strategies as st, settings

from bladerf_receiver import BladeRFReceiver


class TestSampleFormatConversion:
    """Property tests for sample format conversion."""
    
    @given(st.lists(
        st.tuples(
            st.integers(min_value=-2048, max_value=2047),  # I component (12-bit range)
            st.integers(min_value=-2048, max_value=2047)   # Q component (12-bit range)
        ),
        min_size=1,
        max_size=1000
    ))
    @settings(max_examples=100)
    def test_sc16_q11_to_complex64_range(self, iq_pairs):
        """
        **Feature: bladerf-a4-refactor, Property 1: Sample Format Conversion**
        **Validates: Requirements 1.5**
        
        For any array of SC16_Q11 formatted samples, converting to complex64 
        format SHALL produce values in the range [-1.0, 1.0].
        """
        # Create SC16_Q11 buffer from I/Q pairs
        buf = bytearray()
        for i_val, q_val in iq_pairs:
            # Pack as little-endian int16
            buf.extend(int(i_val).to_bytes(2, byteorder='little', signed=True))
            buf.extend(int(q_val).to_bytes(2, byteorder='little', signed=True))
        
        # Convert using the BladeRFReceiver method
        samples = BladeRFReceiver._convert_sc16_q11_to_complex64(buf)
        
        # Verify output is complex64
        assert samples.dtype == np.complex64
        
        # Verify all values are in range [-1.0, 1.0]
        assert np.all(np.real(samples) >= -1.0)
        assert np.all(np.real(samples) <= 1.0)
        assert np.all(np.imag(samples) >= -1.0)
        assert np.all(np.imag(samples) <= 1.0)

    @given(st.lists(
        st.tuples(
            st.integers(min_value=-2048, max_value=2047),
            st.integers(min_value=-2048, max_value=2047)
        ),
        min_size=1,
        max_size=1000
    ))
    @settings(max_examples=100)
    def test_sc16_q11_to_complex64_iq_pairing(self, iq_pairs):
        """
        **Feature: bladerf-a4-refactor, Property 1: Sample Format Conversion**
        **Validates: Requirements 1.5**
        
        For any array of SC16_Q11 formatted samples, the I and Q components
        SHALL be correctly paired in the resulting complex64 array.
        """
        # Create SC16_Q11 buffer from I/Q pairs
        buf = bytearray()
        for i_val, q_val in iq_pairs:
            buf.extend(int(i_val).to_bytes(2, byteorder='little', signed=True))
            buf.extend(int(q_val).to_bytes(2, byteorder='little', signed=True))
        
        # Convert using the BladeRFReceiver method
        samples = BladeRFReceiver._convert_sc16_q11_to_complex64(buf)
        
        # Verify correct number of samples
        assert len(samples) == len(iq_pairs)
        
        # Verify I/Q pairing is correct
        scale_factor = 2048.0
        for idx, (i_val, q_val) in enumerate(iq_pairs):
            expected_i = i_val / scale_factor
            expected_q = q_val / scale_factor
            
            # Use approximate comparison due to float precision
            assert np.isclose(np.real(samples[idx]), expected_i, rtol=1e-5)
            assert np.isclose(np.imag(samples[idx]), expected_q, rtol=1e-5)
    
    @given(st.lists(
        st.tuples(
            st.integers(min_value=-32768, max_value=32767),  # Full int16 range
            st.integers(min_value=-32768, max_value=32767)
        ),
        min_size=1,
        max_size=500
    ))
    @settings(max_examples=100)
    def test_sc16_q11_handles_full_int16_range(self, iq_pairs):
        """
        **Feature: bladerf-a4-refactor, Property 1: Sample Format Conversion**
        **Validates: Requirements 1.5**
        
        For any array of SC16_Q11 formatted samples using the full int16 range,
        conversion SHALL not produce NaN or Inf values.
        """
        # Create SC16_Q11 buffer from I/Q pairs
        buf = bytearray()
        for i_val, q_val in iq_pairs:
            buf.extend(int(i_val).to_bytes(2, byteorder='little', signed=True))
            buf.extend(int(q_val).to_bytes(2, byteorder='little', signed=True))
        
        # Convert using the BladeRFReceiver method
        samples = BladeRFReceiver._convert_sc16_q11_to_complex64(buf)
        
        # Verify no NaN or Inf values
        assert not np.any(np.isnan(samples))
        assert not np.any(np.isinf(samples))
        
        # Verify output is complex64
        assert samples.dtype == np.complex64
