#!/usr/bin/env python3
"""Diagnostic script to test BladeRF receiver and identify issues."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from bladerf_receiver import BladeRFReceiver
from frequency_scanner import FrequencyScanner
import time

def test_device_connection():
    """Test if BladeRF device can be opened."""
    print("=" * 60)
    print("TEST 1: Device Connection")
    print("=" * 60)
    try:
        receiver = BladeRFReceiver(sample_rate=50e6, gain=50)
        print("✓ BladeRF device opened successfully")
        print(f"  Sample rate: {receiver.sample_rate/1e6:.2f} MHz")
        print(f"  Gain: {receiver.gain} dB")
        receiver.close()
        return True
    except Exception as e:
        print(f"✗ Failed to open device: {e}")
        return False

def test_frequency_tuning():
    """Test frequency tuning across all DroneID bands."""
    print("\n" + "=" * 60)
    print("TEST 2: Frequency Tuning")
    print("=" * 60)
    try:
        receiver = BladeRFReceiver(sample_rate=50e6, gain=50)
        scanner = FrequencyScanner(receiver=receiver)
        
        test_freqs = [2414.5e6, 2474.5e6, 5721.5e6, 5831.5e6]
        
        for freq in test_freqs:
            success = receiver.set_frequency(freq)
            if success:
                print(f"✓ Tuned to {freq/1e6:.1f} MHz")
            else:
                print(f"✗ Failed to tune to {freq/1e6:.1f} MHz")
        
        receiver.close()
        return True
    except Exception as e:
        print(f"✗ Frequency tuning failed: {e}")
        return False

def test_sample_reception():
    """Test receiving samples."""
    print("\n" + "=" * 60)
    print("TEST 3: Sample Reception")
    print("=" * 60)
    try:
        receiver = BladeRFReceiver(sample_rate=50e6, gain=50)
        receiver.set_frequency(2414.5e6)
        
        print("Receiving 1 second of samples...")
        start_time = time.time()
        samples = receiver.receive_samples(int(50e6))  # 1 second
        elapsed = time.time() - start_time
        
        if len(samples) > 0:
            print(f"✓ Received {len(samples)} samples in {elapsed:.2f} seconds")
            print(f"  Sample rate achieved: {len(samples)/elapsed/1e6:.2f} MHz")
            print(f"  Sample dtype: {samples.dtype}")
            print(f"  Sample range: [{samples.real.min():.3f}, {samples.real.max():.3f}]")
            
            # Check for signal power
            power = np.mean(np.abs(samples)**2)
            power_db = 10 * np.log10(power + 1e-12)
            print(f"  Average power: {power_db:.1f} dB")
            
            if power_db < -60:
                print("  ⚠ WARNING: Very low signal power - check antenna connection")
        else:
            print("✗ No samples received")
            return False
        
        receiver.close()
        return True
    except Exception as e:
        print(f"✗ Sample reception failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_detection():
    """Test for any RF activity."""
    print("\n" + "=" * 60)
    print("TEST 4: Signal Detection (10 seconds)")
    print("=" * 60)
    try:
        receiver = BladeRFReceiver(sample_rate=50e6, gain=50)
        scanner = FrequencyScanner(receiver=receiver)
        
        print("Scanning all DroneID frequencies...")
        print("(Make sure drones are powered on and flying nearby)")
        
        all_freqs = scanner.FREQUENCIES_2_4GHZ + scanner.FREQUENCIES_5_8GHZ
        
        for freq in all_freqs:
            receiver.set_frequency(freq)
            print(f"\n  Scanning {freq/1e6:.1f} MHz...", end=" ", flush=True)
            
            # Receive 0.5 seconds
            samples = receiver.receive_samples(int(0.5 * 50e6))
            
            if len(samples) > 0:
                power = np.mean(np.abs(samples)**2)
                power_db = 10 * np.log10(power + 1e-12)
                
                # Check for peaks (potential signals)
                threshold = np.mean(np.abs(samples)) + 3 * np.std(np.abs(samples))
                peaks = np.sum(np.abs(samples) > threshold)
                
                print(f"Power: {power_db:.1f} dB, Peaks: {peaks}")
                
                if peaks > 100:
                    print(f"    ⚠ Possible signal activity detected!")
            else:
                print("No samples")
        
        receiver.close()
        return True
    except Exception as e:
        print(f"✗ Signal detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "BladeRF DroneID Receiver Diagnostics" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        test_device_connection,
        test_frequency_tuning,
        test_sample_reception,
        test_signal_detection
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except KeyboardInterrupt:
            print("\n\nDiagnostics interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        print("\nIf you're still not detecting drones, try:")
        print("  1. Use --legacy flag for Mavic 2: python src/droneid_receiver_live.py --legacy")
        print("  2. Increase gain: python src/droneid_receiver_live.py --gain 60")
        print("  3. Make sure drones are flying (not just powered on)")
        print("  4. Check antenna is properly connected")
    else:
        print("\n✗ Some tests failed - see errors above")
    
    print()

if __name__ == "__main__":
    main()
