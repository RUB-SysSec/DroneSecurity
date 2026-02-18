# Quick Reference Card

## Installation Checklist

### Windows
- [ ] Python 3.8-3.11 installed (64-bit)
- [ ] GNU Radio 3.10+ (Radioconda recommended)
- [ ] BladeRF drivers (Zadig → WinUSB)
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] USB 3.0 port (blue port)
- [ ] USB power management disabled

### Linux
- [ ] Python 3.8+ installed
- [ ] GNU Radio + gr-osmosdr (`sudo apt install gnuradio gr-osmosdr`)
- [ ] BladeRF or UHD installed
- [ ] USB permissions configured (udev rules)
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Performance tuning (optional)

---

## Common Commands

### Live Receiver

```bash
# Basic usage (Windows)
python src\droneid_receiver_live.py --gain 55

# Basic usage (Linux)
python src/droneid_receiver_live.py --gain 55

# 2.4 GHz only (faster scanning)
python src/droneid_receiver_live.py --gain 55 --band-2-4-only

# Legacy drones (Mavic 2, Mavic Pro)
python src/droneid_receiver_live.py --gain 55 --legacy

# Adjust gain (0=AGC, 1-60=manual)
python src/droneid_receiver_live.py --gain 40

# Reduce workers (lower CPU usage)
python src/droneid_receiver_live.py --gain 55 --workers 1

# Shorter capture duration (faster scanning)
python src/droneid_receiver_live.py --gain 55 --duration 0.8

# Enable file saving (disabled by default)
python src/droneid_receiver_live.py --gain 55 --save-files

# Custom output directory (e.g., RAM disk)
python src/droneid_receiver_live.py --gain 55 --output-dir R:\droneid

# Verbose output
python src/droneid_receiver_live.py --gain 55 --verbose

# Debug mode
python src/droneid_receiver_live.py --gain 55 --debug
```

### Offline Decoder

```bash
# Decode sample file
python src/droneid_receiver_offline.py -i samples/mini2_sm

# With debug output
python src/droneid_receiver_offline.py -i samples/mini2_sm --debug

# Legacy mode
python src/droneid_receiver_offline.py -i samples/mavic_air_2 --legacy

# Custom sample rate
python src/droneid_receiver_offline.py -i capture.raw -s 50e6

# With GUI (Linux only)
python src/droneid_receiver_offline.py -i samples/mini2_sm --gui
```

### Diagnostics

```bash
# Test hardware
python src/diagnose_receiver.py

# Check BladeRF
python -c "from bladerf import _bladerf; sdr = _bladerf.BladeRF(); print('Serial:', sdr.serial)"

# Check GNU Radio
python -c "from gnuradio import gr; print('GNU Radio:', gr.version())"

# Check osmosdr
python -c "import osmosdr; print('osmosdr OK')"

# List USB devices (Linux)
lsusb | grep -i "nuand\|ettus"

# Check BladeRF CLI (Linux)
bladeRF-cli -p
```

---

## Troubleshooting Quick Fixes

### "Device not found"
```bash
# Windows: Check Zadig driver installation
# Linux: Check USB permissions and udev rules
# Both: Try different USB port (USB 3.0 blue port)
```

### "Sample drops" / "USB errors"
```bash
# 1. Use USB 3.0 port (critical!)
# 2. Disable USB power management
# 3. Close background applications
# 4. Reduce workers: --workers 1
# 5. Use Linux (best solution)
```

### "High CPU usage"
```bash
# Reduce workers
python src/droneid_receiver_live.py --workers 1

# Shorter duration
python src/droneid_receiver_live.py --duration 0.8

# Close other applications
```

### "No packets detected"
```bash
# 1. Verify drone is powered on and connected to controller
# 2. Increase gain: --gain 60
# 3. Try legacy mode: --legacy
# 4. Move antenna closer to drone (1-2 meters)
# 5. Check antenna connection
```

### "CRC errors"
```bash
# 1. Increase gain
# 2. Move antenna closer
# 3. Check antenna orientation
# 4. Reduce interference sources
```

### "ImportError: No module named 'osmosdr'"
```bash
# Windows: Install GNU Radio (Radioconda)
# Linux: sudo apt install gr-osmosdr
# Both: Verify virtual environment is activated
```

---

## Optimal Settings

### For Best Performance
```bash
# Linux with performance tuning
sudo cpupower frequency-set -g performance
python src/droneid_receiver_live.py --gain 55 --band-2-4-only --workers 2
```

### For Low-End Hardware
```bash
# Reduce CPU usage
python src/droneid_receiver_live.py --gain 55 --workers 1 --duration 0.8
```

### For Maximum Range
```bash
# High gain, longer duration
python src/droneid_receiver_live.py --gain 60 --duration 2.0
```

### For Fast Scanning
```bash
# 2.4 GHz only, short duration
python src/droneid_receiver_live.py --gain 55 --band-2-4-only --duration 0.8
```

---

## Gain Settings Guide

| Gain | Use Case | Range | Noise |
|------|----------|-------|-------|
| 0 | AGC (automatic) | Variable | Low |
| 30 | Default | Medium | Low |
| 40 | Weak signals | Medium-High | Medium |
| 55 | Recommended | High | Medium-High |
| 60 | Maximum | Maximum | High |

**Recommendation:** Start with 55, adjust based on results.

---

## Frequency Bands

### 2.4 GHz Band (Default)
- 2414.5 MHz
- 2429.5 MHz
- 2434.5 MHz
- 2444.5 MHz
- 2459.5 MHz
- 2474.5 MHz

### 5.8 GHz Band (Optional)
- 5721.5 - 5831.5 MHz (10 frequencies)
- Use `--band-2-4-only` to skip 5.8 GHz

---

## Output Format

### JSON Telemetry
```json
{
  "timestamp": "2026-02-18T14:37:03.123456",
  "reception_time_utc": "2026-02-18T09:37:03.123456Z",
  "frequency_mhz": 2444.5,
  "telemetry": {
    "serial_number": "3NZCK1A0445Q5L",
    "device_type": "Mini 2",
    "position": {
      "latitude": 33.9607466782786,
      "longitude": 71.57866420676892,
      "altitude_m": 125.5,
      "height_m": 50.2
    },
    "velocity": {
      "north": 5,
      "east": -2,
      "up": 1
    },
    "home_position": {
      "latitude": 33.9600000000000,
      "longitude": 71.5780000000000
    },
    "operator_position": {
      "latitude": 33.9607466782786,
      "longitude": 71.57866420676892
    },
    "gps_time": 1723542961753,
    "sequence_number": 3031,
    "uuid": "1770032869329911808"
  },
  "crc_valid": true
}
```

---

## File Locations

### Output Files (when --save-files enabled)
- `decoded_bits_MMDD_HHMM.bin` - Decoded bits
- `ext_drone_id_50000000_MMDD_HHMM.raw` - Raw samples (last 10 packets)
- `receive_test_MMDD_HHMM.raw` - Debug samples (latest capture)

### Sample Files
- `samples/mini2_sm` - DJI Mini 2 sample
- `samples/mavic_air_2` - DJI Mavic Air 2 sample

### Documentation
- `README.md` - Main documentation
- `SYSTEM_OVERVIEW.md` - System architecture
- `INSTALLATION_GUIDE_WINDOWS.md` - Windows setup
- `INSTALLATION_GUIDE_LINUX.md` - Linux setup
- `PLATFORM_COMPARISON.md` - Windows vs Linux
- `QUICK_REFERENCE.md` - This file

---

## Supported Drones

### Standard Mode (Default)
- ✅ DJI Mini 2
- ✅ DJI Air 2
- ✅ DJI Air 2S
- ✅ DJI Mini SE
- ✅ DJI Mavic 3
- ✅ DJI FPV

### Legacy Mode (--legacy flag)
- ✅ DJI Mavic 2
- ✅ DJI Mavic Pro
- ✅ DJI Mavic Air
- ✅ DJI Phantom 4 Pro

---

## Performance Expectations

### Linux (Optimal)
- Sample drops: < 0.01%
- Latency: 1-2 ms
- CPU usage: 60-70%
- Success rate: > 95%
- Scan time: ~1.4s per frequency

### Windows (Good)
- Sample drops: 0.1-1%
- Latency: 5-10 ms
- CPU usage: 70-80%
- Success rate: 80-90%
- Scan time: ~1.4s per frequency

---

## Getting Help

1. **Check documentation:**
   - [INSTALLATION_GUIDE_WINDOWS.md](INSTALLATION_GUIDE_WINDOWS.md)
   - [INSTALLATION_GUIDE_LINUX.md](INSTALLATION_GUIDE_LINUX.md)
   - [PLATFORM_COMPARISON.md](PLATFORM_COMPARISON.md)
   - [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)

2. **Run diagnostics:**
   ```bash
   python src/diagnose_receiver.py
   ```

3. **Check GitHub Issues:**
   - https://github.com/Skeletoskull/DroneSecurity/issues

4. **Original paper:**
   - https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf

---

**Keep this reference handy for quick lookups!** 📋
