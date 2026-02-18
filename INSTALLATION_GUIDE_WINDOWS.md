# Complete Installation Guide - Windows

This guide walks you through installing all required software for the DJI DroneID receiver on Windows.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [GNU Radio Installation](#gnu-radio-installation)
4. [BladeRF Drivers](#bladerf-drivers)
5. [Python Dependencies](#python-dependencies)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS:** Windows 10 (64-bit) or Windows 11
- **CPU:** Intel Core i5 or AMD Ryzen 5 (4+ cores recommended)
- **RAM:** 8 GB minimum, 16 GB recommended
- **USB:** USB 3.0 port (blue port) - **CRITICAL**
- **Storage:** 5 GB free space
- **SDR:** BladeRF A4 or BladeRF 2.0 micro xA4

### Recommended Requirements
- **CPU:** Intel Core i7/i9 or AMD Ryzen 7/9 (8+ cores)
- **RAM:** 16-32 GB
- **USB:** Dedicated USB 3.0 controller (not shared hub)
- **Storage:** SSD with 10+ GB free space
- **OS:** Windows 11 with latest updates

### Why These Requirements?

**CPU:** Real-time signal processing at 50 MHz sample rate requires significant computational power:
- STFT analysis: ~30% CPU per core
- OFDM demodulation: ~20% CPU per core
- QPSK decoding: ~15% CPU per core
- With 2 worker processes, expect 60-80% total CPU usage

**RAM:** Sample buffers and processing:
- 1.3 seconds @ 50 MHz = 65M samples = ~520 MB per capture
- Multiple buffers in queue = 1-2 GB RAM usage
- GNU Radio overhead = 500 MB - 1 GB
- Total: 4-6 GB during operation

**USB 3.0:** Bandwidth requirements:
- 50 MHz sample rate × 2 bytes/sample (I) × 2 bytes/sample (Q) = 200 MB/s
- USB 2.0 max: ~40 MB/s (too slow!)
- USB 3.0 max: ~400 MB/s (sufficient)
- **Using USB 2.0 will cause sample drops and failed decoding**

---

## Python Installation

### Step 1: Download Python

1. Go to: https://www.python.org/downloads/windows/
2. Download **Python 3.11.x** (64-bit) - Recommended version
   - Also compatible: Python 3.8, 3.9, 3.10
   - **Avoid Python 3.12+** (some dependencies may not be compatible yet)

### Step 2: Install Python

1. Run the installer
2. **CRITICAL:** Check ✅ "Add Python to PATH"
3. Click "Install Now"
4. Wait for installation to complete
5. Click "Disable path length limit" (if prompted)

### Step 3: Verify Installation

```powershell
# Check Python version
python --version
# Should show: Python 3.11.x

# Check pip (package manager)
pip --version
# Should show: pip 23.x.x from ...

# Verify 64-bit Python
python -c "import struct; print(struct.calcsize('P') * 8)"
# Should show: 64
```

### Step 4: Upgrade pip

```powershell
python -m pip install --upgrade pip setuptools wheel
```

---

## GNU Radio Installation

GNU Radio is **required** for SDR hardware abstraction. It provides the `osmosdr` source block that interfaces with BladeRF.

### Why GNU Radio?

**GNU Radio provides:**
- Hardware abstraction layer (osmosdr)
- Sample format conversion (SC16_Q11 → Complex64)
- USB streaming management
- Buffer management
- Device discovery and configuration

**Without GNU Radio:**
- You'd need to write low-level BladeRF API code
- Manual sample format conversion
- Manual USB buffer management
- Platform-specific code for each SDR

### Installation Methods

#### Method 1: Radioconda (Recommended - Easiest)

Radioconda is a conda distribution with GNU Radio pre-installed.

```powershell
# Download Radioconda installer
# Go to: https://github.com/ryanvolz/radioconda/releases
# Download: radioconda-2023.11.0-Windows-x86_64.exe

# Run the installer
# - Install for: Just Me
# - Destination: C:\Users\<YourName>\radioconda3
# - Add to PATH: Yes

# Restart PowerShell

# Verify installation
conda --version
# Should show: conda 23.x.x

# Activate radioconda environment
conda activate base

# Verify GNU Radio
python -c "import osmosdr; print('GNU Radio osmosdr OK')"
# Should show: GNU Radio osmosdr OK
```

#### Method 2: Pre-built Binaries (Alternative)

```powershell
# Download from: https://wiki.gnuradio.org/index.php/WindowsInstall
# Choose: gnuradio_3.10.x_win64.msi

# Run the installer
# - Accept defaults
# - Install to: C:\Program Files\GNURadio-3.10

# Add to PATH manually:
# 1. Open System Properties → Environment Variables
# 2. Edit "Path" variable
# 3. Add: C:\Program Files\GNURadio-3.10\bin
# 4. Add: C:\Program Files\GNURadio-3.10\lib\site-packages

# Restart PowerShell

# Verify
python -c "import osmosdr; print('GNU Radio OK')"
```

#### Method 3: Build from Source (Advanced - Not Recommended)

Building GNU Radio from source on Windows is complex and time-consuming. Only attempt if you have experience with:
- CMake
- Visual Studio C++ compiler
- Dependency management
- Windows development

See: https://wiki.gnuradio.org/index.php/BuildingGNURadioOnWindows

### Verify GNU Radio Installation

```powershell
# Check GNU Radio version
python -c "from gnuradio import gr; print(gr.version())"
# Should show: 3.10.x.x

# Check osmosdr (critical for BladeRF)
python -c "import osmosdr; print('osmosdr version:', osmosdr.version())"
# Should show: osmosdr version: 0.2.x

# List available SDR sources
python -c "import osmosdr; src = osmosdr.source(); print('SDR support OK')"
# Should not error
```

---

## BladeRF Drivers

### Why Drivers Are Needed

BladeRF uses **libusb** for USB communication. Windows requires a specific USB driver (WinUSB) to allow libusb to access the device.

**Without proper drivers:**
- Device not recognized
- "No device found" errors
- USB communication failures

### Step 1: Download Zadig

Zadig is a tool that installs USB drivers for libusb devices.

1. Go to: https://zadig.akeo.ie/
2. Download: **Zadig 2.8** (or latest)
3. No installation needed - it's portable

### Step 2: Connect BladeRF

1. Connect BladeRF A4 to **USB 3.0 port** (blue port)
2. Wait for Windows to detect the device
3. Device may show as "Unknown Device" in Device Manager - this is normal

### Step 3: Install WinUSB Driver

1. **Run Zadig as Administrator** (right-click → Run as administrator)
2. Click **Options → List All Devices**
3. Select **"Nuand bladeRF"** from dropdown
   - If not visible, try unplugging and replugging the device
   - May show as "Nuand bladeRF 2.0" or "bladeRF A4"
4. Verify:
   - USB ID shows: `2CF0 5250` (or similar)
   - Driver shows: `(NONE)` or `(WinUSB)` or other
5. Select **WinUSB** as target driver (right side)
6. Click **"Install Driver"** or **"Replace Driver"**
7. Wait for installation (30-60 seconds)
8. Success message should appear

### Step 4: Verify Driver Installation

```powershell
# Check if BladeRF is detected
python -c "from bladerf import _bladerf; sdr = _bladerf.BladeRF(); print('BladeRF detected:', sdr.serial)"
# Should show: BladeRF detected: <serial number>

# If error, try:
python -c "import osmosdr; src = osmosdr.source('bladerf=0'); print('BladeRF OK')"
```

### Troubleshooting Driver Issues

**"Device not found":**
- Verify USB 3.0 port (blue port)
- Try different USB port
- Unplug, wait 10 seconds, replug
- Check Device Manager for "Unknown Device"
- Reinstall driver with Zadig

**"Access denied":**
- Run Zadig as Administrator
- Disable antivirus temporarily
- Check Windows permissions

**"Driver installation failed":**
- Disable Driver Signature Enforcement:
  1. Restart Windows
  2. Hold Shift while clicking Restart
  3. Troubleshoot → Advanced → Startup Settings → Restart
  4. Press F7 for "Disable driver signature enforcement"
  5. Try Zadig again

---

## Python Dependencies

### Step 1: Create Virtual Environment

**Why use a virtual environment?**
- Isolates project dependencies
- Prevents conflicts with other Python projects
- Easy to recreate if something breaks
- Doesn't pollute system Python

```powershell
# Navigate to project directory
cd "D:\Drone Classifier\BladeRF"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Your prompt should now show: (.venv)
```

### Step 2: Install Dependencies

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will install:
# - numpy (numerical computing)
# - scipy (signal processing)
# - matplotlib (plotting)
# - bitarray (bit manipulation)
# - crcmod (CRC calculation)
# - bladerf (BladeRF Python bindings)
# - hypothesis (property-based testing)
# - pytest (testing framework)
```

### Step 3: Verify Dependencies

```powershell
# Check installed packages
pip list

# Verify critical packages
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
python -c "from bladerf import _bladerf; print('BladeRF bindings OK')"
python -c "import osmosdr; print('osmosdr OK')"
```

### Dependency Details

#### Core Dependencies

**numpy (≥1.22.0)**
- Purpose: Array operations, FFT, numerical computing
- Why needed: All signal processing uses numpy arrays
- Size: ~50 MB

**scipy (≥1.8.0)**
- Purpose: Signal processing (STFT, resampling, filtering)
- Why needed: Packet detection, frequency estimation
- Size: ~100 MB

**matplotlib (≥3.5.0)**
- Purpose: Plotting and visualization
- Why needed: Debug mode spectrum plots
- Size: ~50 MB

**bitarray (≥2.4.0)**
- Purpose: Bit-level operations
- Why needed: QPSK symbol to bit conversion
- Size: ~1 MB

**crcmod (≥1.7)**
- Purpose: CRC calculation
- Why needed: DroneID packet validation
- Size: <1 MB

#### SDR Dependencies

**bladerf**
- Purpose: Python bindings for BladeRF hardware
- Why needed: Direct hardware control (alternative to osmosdr)
- Size: ~5 MB
- Note: Requires libbladeRF installed

**GNU Radio (osmosdr)**
- Purpose: SDR hardware abstraction
- Why needed: Sample streaming from BladeRF
- Size: ~500 MB (full GNU Radio installation)
- Note: Installed separately (see GNU Radio section)

#### Testing Dependencies

**hypothesis (≥6.0.0)**
- Purpose: Property-based testing
- Why needed: Automated test generation
- Size: ~5 MB
- Optional: Only needed for development

**pytest (≥7.0.0)**
- Purpose: Test framework
- Why needed: Running test suite
- Size: ~5 MB
- Optional: Only needed for development

---

## Verification

### Complete System Check

Run this comprehensive test to verify everything is working:

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Run system diagnostics
python src\diagnose_receiver.py

# This will test:
# 1. BladeRF device detection
# 2. Frequency tuning
# 3. Sample reception
# 4. Signal processing pipeline
```

### Manual Verification Steps

```powershell
# 1. Check Python
python --version
# Expected: Python 3.8.x - 3.11.x

# 2. Check GNU Radio
python -c "from gnuradio import gr; print('GNU Radio:', gr.version())"
# Expected: GNU Radio: 3.10.x.x

# 3. Check osmosdr
python -c "import osmosdr; print('osmosdr OK')"
# Expected: osmosdr OK

# 4. Check BladeRF
python -c "from bladerf import _bladerf; sdr = _bladerf.BladeRF(); print('Serial:', sdr.serial)"
# Expected: Serial: <your device serial>

# 5. Check NumPy
python -c "import numpy; print('NumPy:', numpy.__version__)"
# Expected: NumPy: 1.22.x or higher

# 6. Check SciPy
python -c "import scipy; print('SciPy:', scipy.__version__)"
# Expected: SciPy: 1.8.x or higher

# 7. Test offline decoder (no hardware needed)
python src\droneid_receiver_offline.py -i samples\mini2_sm
# Expected: Should decode sample file and show JSON output
```

### Test Live Receiver

```powershell
# Test with real hardware (drone must be flying nearby)
python src\droneid_receiver_live.py --gain 55 --duration 2.0

# Expected output:
# BladeRF initialized: 50.00 MHz sample rate
# Start receiving...
# Scanning: 2414.50 MHz @ 50.00 MHz
# [If drone detected, will show JSON telemetry]
```

---

## Troubleshooting

### Python Issues

**"python: command not found"**
```powershell
# Python not in PATH
# Reinstall Python and check "Add to PATH"
# Or add manually:
# C:\Users\<YourName>\AppData\Local\Programs\Python\Python311
# C:\Users\<YourName>\AppData\Local\Programs\Python\Python311\Scripts
```

**"pip: command not found"**
```powershell
# Use python -m pip instead
python -m pip install <package>
```

**"Permission denied"**
```powershell
# Run PowerShell as Administrator
# Or install packages with --user flag
pip install --user <package>
```

### GNU Radio Issues

**"ImportError: No module named osmosdr"**
```powershell
# GNU Radio not installed or not in PATH
# Verify installation:
where python
# Should show path inside radioconda or GNU Radio directory

# If using radioconda:
conda activate base

# If using standalone GNU Radio:
# Add to PATH: C:\Program Files\GNURadio-3.10\lib\site-packages
```

**"DLL load failed"**
```powershell
# Missing Visual C++ Redistributables
# Download and install:
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### BladeRF Issues

**"Device not found"**
```powershell
# 1. Check USB connection (USB 3.0 port)
# 2. Verify driver with Zadig
# 3. Try different USB port
# 4. Restart computer
# 5. Check Device Manager for "Unknown Device"
```

**"Device busy"**
```powershell
# Another application is using BladeRF
# Close: SDR#, GQRX, GNU Radio Companion, etc.
# Or restart computer
```

**"USB communication error"**
```powershell
# 1. Use USB 3.0 port (blue port)
# 2. Avoid USB hubs
# 3. Update USB 3.0 drivers
# 4. Try different USB cable
# 5. Check USB power management:
#    Device Manager → USB Root Hub → Power Management
#    Uncheck "Allow computer to turn off this device"
```

### Dependency Issues

**"No module named 'numpy'"**
```powershell
# Virtual environment not activated
.venv\Scripts\activate

# Or install in system Python
pip install numpy
```

**"ImportError: DLL load failed"**
```powershell
# Missing Visual C++ Redistributables
# Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
# Install and restart
```

**"Version conflict"**
```powershell
# Recreate virtual environment
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Performance Issues

**"High CPU usage"**
```powershell
# Reduce worker count
python src\droneid_receiver_live.py --workers 1

# Reduce sample duration
python src\droneid_receiver_live.py --duration 1.0

# Disable file saving (already default)
python src\droneid_receiver_live.py  # files disabled by default
```

**"Sample drops / USB errors"**
```powershell
# 1. Use USB 3.0 port (critical!)
# 2. Close other applications
# 3. Disable USB power management
# 4. Use dedicated USB controller (not shared hub)
# 5. Reduce sample rate (not recommended):
#    python src\droneid_receiver_live.py --sample-rate 40e6
```

**"Out of memory"**
```powershell
# Reduce sample duration
python src\droneid_receiver_live.py --duration 0.8

# Reduce worker count
python src\droneid_receiver_live.py --workers 1

# Close other applications
# Upgrade RAM to 16 GB
```

---

## Installation Time Estimates

- **Python:** 5 minutes
- **GNU Radio (Radioconda):** 15-20 minutes
- **BladeRF Drivers:** 5 minutes
- **Python Dependencies:** 5-10 minutes
- **Verification:** 5 minutes

**Total:** ~45-60 minutes for complete setup

---

## Next Steps

After successful installation:

1. ✅ Test offline decoder: `python src\droneid_receiver_offline.py -i samples\mini2_sm`
2. ✅ Test hardware: `python src\diagnose_receiver.py`
3. ✅ Run live receiver: `python src\droneid_receiver_live.py --gain 55`
4. ✅ Read documentation: `SYSTEM_OVERVIEW.md`
5. ✅ Adjust settings for your environment

---

## Getting Help

If you encounter issues:

1. **Check this troubleshooting section**
2. **Run diagnostics:** `python src\diagnose_receiver.py`
3. **Check GitHub Issues:** https://github.com/Skeletoskull/DroneSecurity/issues
4. **GNU Radio Help:** https://wiki.gnuradio.org/
5. **BladeRF Help:** https://www.nuand.com/support/

---

**Installation complete! You're ready to receive DroneID signals.** 🎉
