# DJI Drone-ID Live Receiver Signal Processing Pipeline

## Overview
The live receiver implements a real-time signal processing pipeline to decode DJI's proprietary Drone-ID protocol from OcuSync 2.0 transmissions using software-defined radio (SDR).

## Signal Flow Architecture

### 1. RF Signal Acquisition
**File:** `src/droneid_receiver_live.py` - `receive_thread()`
- **Hardware:** Ettus USRP B205-mini SDR
- **Frequency Hopping:** Scans predefined frequency list:
  - 2.4 GHz: [2414.5, 2429.5, 2434.5, 2444.5, 2459.5, 2474.5] MHz
  - 5.8 GHz: [5721.5, 5731.5, 5741.5, 5756.5, 5761.5, 5771.5, 5786.5, 5801.5, 5816.5, 5831.5] MHz
- **Sample Rate:** 50 MHz (configurable)
- **Duration:** 1.3 seconds per frequency band
- **Output:** Raw IQ samples (complex64)

### 2. Packet Detection & Coarse Processing
**File:** `src/SpectrumCapture.py` - `SpectrumCapture` class
- **Input:** Raw IQ samples from SDR
- **Detection Method:** Time-domain power analysis using STFT
- **Packet Length Filtering:** 630-665 μs for Drone-ID frames
- **Coarse CFO Estimation:** Initial center frequency offset correction
- **Output:** Individual packet candidates with rough timing

### 3. Fine Synchronization & OFDM Processing  
**File:** `src/Packet.py` - `Packet` class
- **Fine Timing:** Cyclic prefix correlation for precise symbol boundaries
- **Fine CFO Correction:** Frequency offset estimation and correction
- **ZC Sequence Detection:** Finds Zadoff-Chu sequences (600, 147) for synchronization
- **Channel Estimation:** Uses ZC sequences to estimate channel response
- **OFDM Demodulation:** FFT-based symbol extraction (1024-point FFT, 601 carriers)
- **Output:** Equalized frequency-domain OFDM symbols

### 4. QPSK Demodulation & Decoding
**File:** `src/qpsk.py` - `Decoder` class
- **QPSK Mapping:** Brute-force phase alignment (0°, 90°, 180°, 270°)
- **Descrambling:** Gold sequence-based descrambling (seed: 0x12345678)
- **Turbo Decoding:** 3GPP-compliant turbo decoder with rate matching
- **Output:** Raw decoded bits

### 5. Protocol Parsing & Validation
**File:** `src/droneid_packet.py` - `DroneIDPacket` class
- **Struct Unpacking:** 91-byte Drone-ID payload parsing
- **CRC Validation:** 16-bit CRC check (poly: 0x11021, init: 0x3692)
- **Data Extraction:**
  - GPS coordinates (drone & pilot)
  - Altitude, velocity vectors
  - Serial number, device type
  - Timestamps, flight state
- **Output:** JSON-formatted telemetry data

## Threading Architecture
- **Receiver Thread:** Continuous SDR sampling and frequency hopping
- **Worker Processes:** Parallel signal processing (configurable, default: 2)
- **Frequency Locking:** Locks to frequency when Drone-ID detected

## Key Processing Parameters
- **OFDM:** 1024-point FFT, 601 active carriers
- **Cyclic Prefix:** 72-80 samples (LTE-based)
- **Symbol Structure:** 9 symbols total (2 ZC sequences, 7 data symbols)
- **Bandwidth:** ~10 MHz signal bandwidth
- **Resampling:** 50 MHz → 15.36 MHz for OFDM processing

## Performance Characteristics
- **Detection Range:** Depends on RF conditions and drone power
- **Processing Latency:** Near real-time (< 2 seconds)
- **Success Rate:** Varies with signal quality and interference
- **Resource Requirements:** High CPU usage due to 50 MHz sampling

## Output Format
```json
{
    "latitude": 51.446866781640146,
    "longitude": 7.267960786785307,
    "altitude": 39.32,
    "device_type": "Mini 2",
    "serial_number": "SecureStorage?",
    "app_lat": 43.26826445428658,
    "app_lon": 6.640125363111847,
    "sequence_number": 878,
    "gps_time": 1650894901980
}
```

The pipeline successfully reverse-engineered DJI's proprietary protocol, enabling real-time drone tracking and identification for security research purposes.