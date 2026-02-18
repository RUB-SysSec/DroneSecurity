"""Tests for FrequencyScanner including property-based tests.

**Feature: bladerf-a4-refactor**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from frequency_scanner import FrequencyScanner, ScanState


class TestFrequencyLockStateMachine:
    """Property tests for frequency lock state machine.
    
    **Feature: bladerf-a4-refactor, Property 2: Frequency Lock State Machine**
    **Validates: Requirements 2.3, 2.4**
    """
    
    @given(st.lists(
        st.booleans(),
        min_size=1,
        max_size=50
    ))
    @settings(max_examples=100)
    def test_lock_state_machine_behavior(self, detection_sequence):
        """
        **Feature: bladerf-a4-refactor, Property 2: Frequency Lock State Machine**
        **Validates: Requirements 2.3, 2.4**
        
        For any sequence of packet detection results, the FrequencyScanner SHALL
        remain locked to a frequency while packets are detected, and SHALL unlock
        after exactly 10 consecutive scans without detection.
        """
        scanner = FrequencyScanner()
        test_frequency = 2414.5e6
        
        # Lock to a frequency first
        scanner.lock_frequency(test_frequency)
        assert scanner.state == ScanState.LOCKED
        assert scanner.locked_frequency == test_frequency
        
        consecutive_empty = 0
        
        for detected in detection_sequence:
            # Record the detection result
            scanner.record_detection(detected)
            
            if detected:
                # Detection resets the counter
                consecutive_empty = 0
                # Should remain locked
                if scanner.state == ScanState.LOCKED:
                    assert scanner.locked_frequency == test_frequency
            else:
                consecutive_empty += 1
            
            # Check state based on consecutive empty count
            if consecutive_empty >= 10:
                # Should have unlocked
                assert scanner.state == ScanState.SCANNING
                assert scanner.locked_frequency is None
                # Once unlocked, further detections don't re-lock automatically
                break
            else:
                # Should still be locked (if we haven't unlocked yet)
                if scanner.state == ScanState.LOCKED:
                    assert scanner.empty_scan_count == consecutive_empty
    
    @given(st.integers(min_value=0, max_value=9))
    @settings(max_examples=100)
    def test_remains_locked_under_threshold(self, num_empty_scans):
        """
        **Feature: bladerf-a4-refactor, Property 2: Frequency Lock State Machine**
        **Validates: Requirements 2.3, 2.4**
        
        For any number of consecutive empty scans less than 10, the scanner
        SHALL remain locked to the frequency.
        """
        scanner = FrequencyScanner()
        test_frequency = 5721.5e6
        
        # Lock to frequency
        scanner.lock_frequency(test_frequency)
        
        # Record empty scans (less than threshold)
        for _ in range(num_empty_scans):
            scanner.record_detection(False)
        
        # Should still be locked
        assert scanner.state == ScanState.LOCKED
        assert scanner.locked_frequency == test_frequency
        assert scanner.empty_scan_count == num_empty_scans
    
    @given(st.integers(min_value=10, max_value=20))
    @settings(max_examples=100)
    def test_unlocks_at_threshold(self, num_empty_scans):
        """
        **Feature: bladerf-a4-refactor, Property 2: Frequency Lock State Machine**
        **Validates: Requirements 2.4**
        
        For any number of consecutive empty scans >= 10, the scanner
        SHALL unlock and resume scanning.
        """
        scanner = FrequencyScanner()
        test_frequency = 2444.5e6
        
        # Lock to frequency
        scanner.lock_frequency(test_frequency)
        
        # Record empty scans (at or above threshold)
        for _ in range(num_empty_scans):
            scanner.record_detection(False)
        
        # Should be unlocked
        assert scanner.state == ScanState.SCANNING
        assert scanner.locked_frequency is None
    
    @given(st.lists(
        st.booleans(),
        min_size=1,
        max_size=20
    ))
    @settings(max_examples=100)
    def test_detection_resets_counter(self, pre_detection_empties):
        """
        **Feature: bladerf-a4-refactor, Property 2: Frequency Lock State Machine**
        **Validates: Requirements 2.3**
        
        For any sequence of empty scans followed by a detection, the empty
        scan counter SHALL reset to 0.
        """
        scanner = FrequencyScanner()
        test_frequency = 2459.5e6
        
        # Lock to frequency
        scanner.lock_frequency(test_frequency)
        
        # Count how many empties before we'd unlock
        empties_before_unlock = min(len(pre_detection_empties), 9)
        
        # Record some empty scans (but not enough to unlock)
        for i, is_empty in enumerate(pre_detection_empties[:9]):
            if not is_empty:
                break
            scanner.record_detection(False)
        
        # If still locked, record a detection
        if scanner.state == ScanState.LOCKED:
            scanner.record_detection(True)
            
            # Counter should be reset
            assert scanner.empty_scan_count == 0
            assert scanner.state == ScanState.LOCKED


class TestSampleDurationCalculation:
    """Property tests for sample duration calculation.
    
    **Feature: bladerf-a4-refactor, Property 3: Sample Duration Calculation**
    **Validates: Requirements 2.5**
    """
    
    @given(
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1e6, max_value=100e6, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_sample_count_equals_duration_times_rate(self, duration, sample_rate):
        """
        **Feature: bladerf-a4-refactor, Property 3: Sample Duration Calculation**
        **Validates: Requirements 2.5**
        
        For any configured duration and sample rate, the number of samples
        captured SHALL equal duration × sample_rate (within rounding tolerance).
        """
        scanner = FrequencyScanner(duration=duration, sample_rate=sample_rate)
        
        num_samples = scanner.calculate_num_samples()
        expected = duration * sample_rate
        
        # Should be within 1 sample of expected (due to int truncation)
        assert abs(num_samples - expected) < 1.0
        
        # Should be exactly int(duration * sample_rate)
        assert num_samples == int(expected)
    
    @given(
        st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1e6, max_value=100e6, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_sample_count_with_override_params(self, duration, sample_rate):
        """
        **Feature: bladerf-a4-refactor, Property 3: Sample Duration Calculation**
        **Validates: Requirements 2.5**
        
        For any duration and sample rate passed as parameters, the calculation
        SHALL use those values instead of instance defaults.
        """
        # Create scanner with different defaults
        scanner = FrequencyScanner(duration=1.0, sample_rate=10e6)
        
        # Calculate with override parameters
        num_samples = scanner.calculate_num_samples(duration=duration, sample_rate=sample_rate)
        expected = int(duration * sample_rate)
        
        assert num_samples == expected
    
    @settings(max_examples=100)
    @given(st.floats(min_value=0.5, max_value=3.0, allow_nan=False, allow_infinity=False))
    def test_default_sample_rate_calculation(self, duration):
        """
        **Feature: bladerf-a4-refactor, Property 3: Sample Duration Calculation**
        **Validates: Requirements 2.5**
        
        For the default 50 MHz sample rate, sample count SHALL be correct.
        """
        scanner = FrequencyScanner(duration=duration)
        
        num_samples = scanner.calculate_num_samples()
        expected = int(duration * 50e6)
        
        assert num_samples == expected


class TestFrequencyListCorrectness:
    """Unit tests for frequency list correctness.
    
    **Validates: Requirements 2.1, 2.2**
    """
    
    def test_2_4ghz_frequencies_correct(self):
        """Test that 2.4 GHz frequency list matches requirements.
        
        **Validates: Requirements 2.1**
        """
        expected = [2414.5e6, 2429.5e6, 2434.5e6, 2444.5e6, 2459.5e6, 2474.5e6]
        assert FrequencyScanner.FREQUENCIES_2_4GHZ == expected
    
    def test_5_8ghz_frequencies_correct(self):
        """Test that 5.8 GHz frequency list matches requirements.
        
        **Validates: Requirements 2.2**
        """
        expected = [
            5721.5e6, 5731.5e6, 5741.5e6, 5756.5e6, 5761.5e6,
            5771.5e6, 5786.5e6, 5801.5e6, 5816.5e6, 5831.5e6
        ]
        assert FrequencyScanner.FREQUENCIES_5_8GHZ == expected
    
    def test_all_frequencies_combined(self):
        """Test that all_frequencies contains both bands."""
        scanner = FrequencyScanner()
        all_freqs = scanner.all_frequencies
        
        # Should contain all 2.4 GHz frequencies
        for freq in FrequencyScanner.FREQUENCIES_2_4GHZ:
            assert freq in all_freqs
        
        # Should contain all 5.8 GHz frequencies
        for freq in FrequencyScanner.FREQUENCIES_5_8GHZ:
            assert freq in all_freqs
        
        # Total count should be sum of both bands
        expected_count = len(FrequencyScanner.FREQUENCIES_2_4GHZ) + len(FrequencyScanner.FREQUENCIES_5_8GHZ)
        assert len(all_freqs) == expected_count


class TestLockUnlockTransitions:
    """Unit tests for lock/unlock state transitions.
    
    **Validates: Requirements 2.3, 2.4**
    """
    
    def test_initial_state_is_scanning(self):
        """Test that scanner starts in SCANNING state."""
        scanner = FrequencyScanner()
        assert scanner.state == ScanState.SCANNING
        assert scanner.locked_frequency is None
    
    def test_lock_frequency_changes_state(self):
        """Test that lock_frequency transitions to LOCKED state.
        
        **Validates: Requirements 2.3**
        """
        scanner = FrequencyScanner()
        test_freq = 2414.5e6
        
        scanner.lock_frequency(test_freq)
        
        assert scanner.state == ScanState.LOCKED
        assert scanner.locked_frequency == test_freq
        assert scanner.empty_scan_count == 0
    
    def test_unlock_frequency_changes_state(self):
        """Test that unlock_frequency transitions to SCANNING state.
        
        **Validates: Requirements 2.4**
        """
        scanner = FrequencyScanner()
        
        # First lock
        scanner.lock_frequency(2414.5e6)
        assert scanner.state == ScanState.LOCKED
        
        # Then unlock
        scanner.unlock_frequency()
        
        assert scanner.state == ScanState.SCANNING
        assert scanner.locked_frequency is None
        assert scanner.empty_scan_count == 0
    
    def test_get_next_frequency_returns_locked_when_locked(self):
        """Test that get_next_frequency returns locked frequency when locked.
        
        **Validates: Requirements 2.3**
        """
        scanner = FrequencyScanner()
        test_freq = 5721.5e6
        
        scanner.lock_frequency(test_freq)
        
        # Should always return locked frequency
        for _ in range(5):
            assert scanner.get_next_frequency() == test_freq
    
    def test_get_next_frequency_cycles_when_scanning(self):
        """Test that get_next_frequency cycles through all frequencies."""
        scanner = FrequencyScanner()
        all_freqs = scanner.all_frequencies
        
        # Should cycle through all frequencies
        returned_freqs = []
        for _ in range(len(all_freqs)):
            returned_freqs.append(scanner.get_next_frequency())
        
        # Should have returned each frequency once
        assert set(returned_freqs) == set(all_freqs)
    
    def test_exactly_10_empty_scans_unlocks(self):
        """Test that exactly 10 consecutive empty scans triggers unlock.
        
        **Validates: Requirements 2.4**
        """
        scanner = FrequencyScanner()
        scanner.lock_frequency(2414.5e6)
        
        # 9 empty scans should not unlock
        for i in range(9):
            scanner.record_detection(False)
            assert scanner.state == ScanState.LOCKED
            assert scanner.empty_scan_count == i + 1
        
        # 10th empty scan should unlock
        scanner.record_detection(False)
        assert scanner.state == ScanState.SCANNING
        assert scanner.locked_frequency is None
    
    def test_reset_returns_to_initial_state(self):
        """Test that reset() returns scanner to initial state."""
        scanner = FrequencyScanner()
        
        # Modify state
        scanner.lock_frequency(2414.5e6)
        scanner.record_detection(False)
        scanner.record_detection(False)
        
        # Reset
        scanner.reset()
        
        assert scanner.state == ScanState.SCANNING
        assert scanner.locked_frequency is None
        assert scanner.empty_scan_count == 0
