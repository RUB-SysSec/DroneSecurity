# Complete Installation Guide - Linux

This guide walks you through installing all required software for the DJI DroneID receiver on Linux.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [GNU Radio Installation](#gnu-radio-installation)
4. [UHD Installation (for USRP)](#uhd-installation-for-usrp)
5. [BladeRF Installation](#bladerf-installation)
6. [Python Dependencies](#python-dependencies)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS:** Ubuntu 20.04 LTS or newer (or equivalent Debian-based distro)
- **CPU:** Intel Core i5 or AMD Ryzen 5 (4+ cores)
- **RAM:** 8 GB minimum, 16 GB recommended
- **USB:** USB 3.0 port
- **Storage:** 5 GB free space
- **SDR:** BladeRF A4, BladeRF 2.0 micro xA4, or Ettus USRP B205-mini

### Recommended Requirements
- **CPU:** Intel Core i7/i9 or AMD Ryzen 7/9 (8+ cores)
- **RAM:** 16-32 GB
- **USB:** Dedicated USB 3.0 controller
- **Storage:** SSD with 10+ GB free space
- **OS:** Ubuntu 22.04 LTS with latest updates

### Supported Distributions
- ✅ Ubuntu 20.04, 22.04, 24.04
- ✅ Debian 11, 12
- ✅ Fedora 38+
- ✅ Arch Linux (latest)
- ⚠️ Other distros may work but are untested

---

## Python Installation

Most Linux distributions come with Python pre-installed. Verify and upgrade if needed.

### Step 1: Check Python Version

```bash
# Check Python version
python3 --version
# Should show: Python 3.8.x or higher

# Check pip
pip3 --version
# Should show: pip 20.x.x or higher
```

### Step 2: Install Python (if needed)

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-dev
```

#### Fedora
```bash
sudo dnf install python3 python3-pip python3-devel
```

#### Arch Linux
```bash
sudo pacman -S python python-pip
```

### Step 3: Verify Installation

```bash
python3 --version  # Should show 3.8.x or higher
pip3 --version     # Should show pip version
```

---

## GNU Radio Installation

GNU Radio is **required** for SDR hardware abstraction.

### Why GNU Radio on Linux is Better

**Linux advantages:**
- Native support (developed primarily for Linux)
- Better USB performance (native libusb)
- Lower latency
- More stable drivers
- Better real-time scheduling
- Easier installation

### Installation Methods

#### Method 1: Package Manager (Recommended)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install gnuradio gr-osmosdr
```

**Fedora:**
```bash
sudo dnf install gnuradio gr-osmosdr
```

**Arch Linux:**
```bash
sudo pacman -S gnuradio gnuradio-osmosdr
```

#### Method 2: PyBOMBS (Advanced)

PyBOMBS builds GNU Radio from source with optimizations.

```bash
# Install PyBOMBS
pip3 install --user pybombs

# Add to PATH
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc

# Add recipes
pybombs recipes add gr-recipes git+https://github.com/gnuradio/gr-recipes.git
pybombs recipes add gr-etcetera git+https://github.com/gnuradio/gr-etcetera.git

# Create prefix
pybombs prefix init ~/gnuradio -a default -R gnuradio-default

# Install GNU Radio
pybombs install gnuradio gr-osmosdr

# Setup environment
source ~/gnuradio/setup_env.sh
echo 'source ~/gnuradio/setup_env.sh' >> ~/.bashrc
```

### Verify GNU Radio Installation

```bash
# Check GNU Radio version
python3 -c "from gnuradio import gr; print('GNU Radio:', gr.version())"
# Should show: GNU Radio: 3.10.x.x

# Check osmosdr
python3 -c "import osmosdr; print('osmosdr OK')"
# Should show: osmosdr OK
```

---

## UHD Installation (for USRP)

If using Ettus USRP B205-mini (original hardware), install UHD drivers.

### Why UHD?

**UHD (USRP Hardware Driver):**
- Official Ettus Research driver
- Optimized for USRP devices
- Better performance than generic osmosdr
- Required for USRP-specific features

### Installation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install libuhd-dev uhd-host python3-uhd
```

#### Fedora
```bash
sudo dnf install uhd uhd-devel python3-uhd
```

#### Arch Linux
```bash
sudo pacman -S libuhd
```

### Download FPGA Images

```bash
# Download USRP firmware/FPGA images
sudo uhd_images_downloader

# This downloads ~500 MB of images
# Required for USRP to function
```

### Verify UHD Installation

```bash
# Check UHD version
uhd_find_devices
# Should list connected USRP devices

# Test USRP
uhd_usrp_probe
# Should show detailed device information
```

### Set USB Permissions

```bash
# Add udev rules for USRP
sudo cp /usr/lib/uhd/utils/uhd-usrp.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add user to usrp group
sudo usermod -a -G usrp $USER

# Log out and log back in for group changes to take effect
```

---

## BladeRF Installation

If using BladeRF A4 or BladeRF 2.0 micro xA4.

### Why BladeRF on Linux?

**Linux advantages:**
- Native libbladeRF support
- Better USB performance
- No driver installation hassles (unlike Windows)
- Automatic device detection
- Lower latency

### Installation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install bladerf libbladerf-dev bladerf-fpga-hostedxa4 bladerf-fpga-hostedxa9
```

#### Fedora
```bash
sudo dnf install bladeRF libbladeRF-devel
```

#### Arch Linux
```bash
sudo pacman -S bladerf
```

### Set USB Permissions

```bash
# Add udev rules for BladeRF
sudo wget https://www.nuand.com/bladeRF.rules -O /etc/udev/rules.d/88-nuand-bladerf1.rules
sudo wget https://www.nuand.com/bladeRF2.rules -O /etc/udev/rules.d/88-nuand-bladerf2.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add user to plugdev group
sudo usermod -a -G plugdev $USER

# Log out and log back in
```

### Verify BladeRF Installation

```bash
# Check BladeRF CLI
bladeRF-cli --version
# Should show: bladeRF-cli version x.x.x

# List devices
bladeRF-cli -p
# Should show connected BladeRF devices

# Test device
bladeRF-cli -e "info"
# Should show device information
```

---

## Python Dependencies

### Step 1: Create Virtual Environment

```bash
# Navigate to project directory
cd ~/DroneSecurity

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Your prompt should now show: (.venv)
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### Step 3: Verify Dependencies

```bash
# Check installed packages
pip list

# Verify critical packages
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
python -c "from bladerf import _bladerf; print('BladeRF bindings OK')"
python -c "import osmosdr; print('osmosdr OK')"
```

---

## Verification

### Complete System Check

```bash
# Activate virtual environment
source .venv/bin/activate

# Run system diagnostics
python src/diagnose_receiver.py
```

### Manual Verification Steps

```bash
# 1. Check Python
python3 --version

# 2. Check GNU Radio
python -c "from gnuradio import gr; print('GNU Radio:', gr.version())"

# 3. Check osmosdr
python -c "import osmosdr; print('osmosdr OK')"

# 4. Check BladeRF (if using BladeRF)
python -c "from bladerf import _bladerf; sdr = _bladerf.BladeRF(); print('Serial:', sdr.serial)"

# 5. Check UHD (if using USRP)
python -c "import uhd; print('UHD OK')"

# 6. Test offline decoder
python src/droneid_receiver_offline.py -i samples/mini2_sm
```

### Test Live Receiver

**With BladeRF:**
```bash
python src/droneid_receiver_live.py --gain 55 --duration 2.0
```

**With USRP (original):**
```bash
# Original implementation uses USRP by default
python src/droneid_receiver_live.py
```

---

## Troubleshooting

### Python Issues

**"python3: command not found"**
```bash
# Install Python
sudo apt install python3 python3-pip
```

**"pip3: command not found"**
```bash
# Install pip
sudo apt install python3-pip
```

### GNU Radio Issues

**"ImportError: No module named osmosdr"**
```bash
# Install gr-osmosdr
sudo apt install gr-osmosdr

# Or rebuild with PyBOMBS
pybombs install gr-osmosdr
```

**"ImportError: libgnuradio-runtime.so"**
```bash
# Update library cache
sudo ldconfig

# Or add to LD_LIBRARY_PATH
echo 'export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### USB Permission Issues

**"Device not found" or "Permission denied"**
```bash
# Check if device is detected
lsusb | grep -i "nuand\|ettus"

# Add udev rules (see BladeRF/UHD installation sections)

# Add user to groups
sudo usermod -a -G plugdev $USER  # For BladeRF
sudo usermod -a -G usrp $USER     # For USRP

# Log out and log back in
```

### BladeRF Issues

**"Device not found"**
```bash
# Check USB connection
lsusb | grep -i nuand

# Check permissions
ls -l /dev/bus/usb/*/*

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Try as root (temporary test)
sudo python src/droneid_receiver_live.py --gain 55
```

**"FPGA not loaded"**
```bash
# Load FPGA manually
bladeRF-cli -l /usr/share/Nuand/bladeRF/hostedxA4.rbf

# Or install FPGA package
sudo apt install bladerf-fpga-hostedxa4
```

### USRP Issues

**"Device not found"**
```bash
# Check USB connection
lsusb | grep -i ettus

# Find devices
uhd_find_devices

# Probe device
uhd_usrp_probe

# Check permissions
ls -l /dev/bus/usb/*/*
```

**"FPGA images not found"**
```bash
# Download FPGA images
sudo uhd_images_downloader
```

### Performance Issues

**"High CPU usage"**
```bash
# Reduce worker count
python src/droneid_receiver_live.py --workers 1

# Enable CPU governor performance mode
sudo cpupower frequency-set -g performance
```

**"Sample drops"**
```bash
# Increase USB buffer size
echo 0 | sudo tee /sys/module/usbcore/parameters/usbfs_memory_mb

# Disable USB autosuspend
echo -1 | sudo tee /sys/module/usbcore/parameters/autosuspend

# Use real-time priority (advanced)
sudo setcap cap_sys_nice=eip $(which python3)
```

---

## Real-Time Performance Tuning (Advanced)

For best performance, especially with USRP:

### 1. Disable CPU Frequency Scaling

```bash
# Install cpupower
sudo apt install linux-tools-common linux-tools-generic

# Set performance governor
sudo cpupower frequency-set -g performance

# Make permanent
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils
```

### 2. Increase USB Buffer Size

```bash
# Temporary
echo 1000 | sudo tee /sys/module/usbcore/parameters/usbfs_memory_mb

# Permanent (add to /etc/rc.local)
echo 'echo 1000 > /sys/module/usbcore/parameters/usbfs_memory_mb' | sudo tee -a /etc/rc.local
```

### 3. Disable Power Management

```bash
# Disable USB autosuspend
echo -1 | sudo tee /sys/module/usbcore/parameters/autosuspend

# Disable laptop mode
echo 0 | sudo tee /proc/sys/vm/laptop_mode
```

### 4. Use Real-Time Scheduling

```bash
# Allow real-time priority
sudo groupadd realtime
sudo usermod -a -G realtime $USER

# Edit /etc/security/limits.conf
echo '@realtime   -   rtprio     99' | sudo tee -a /etc/security/limits.conf
echo '@realtime   -   memlock    unlimited' | sudo tee -a /etc/security/limits.conf

# Log out and log back in
```

---

## Installation Time Estimates

- **Python:** Already installed (0 minutes)
- **GNU Radio:** 5-10 minutes (package manager)
- **UHD/BladeRF:** 5 minutes
- **Python Dependencies:** 5-10 minutes
- **Verification:** 5 minutes

**Total:** ~20-30 minutes for complete setup

---

## Why Linux is Better for SDR

### Performance Advantages

1. **Native USB Support**
   - Linux has native libusb support
   - Windows requires WinUSB driver layer
   - Result: Lower latency, fewer USB errors

2. **Real-Time Scheduling**
   - Linux supports real-time priorities
   - Windows has limited real-time capabilities
   - Result: More consistent sample timing

3. **Better Memory Management**
   - Linux has better large buffer handling
   - Windows may fragment memory
   - Result: Fewer sample drops

4. **CPU Affinity**
   - Linux allows pinning processes to CPU cores
   - Windows has limited control
   - Result: Better performance on multi-core systems

### Development Advantages

1. **Native GNU Radio**
   - Developed primarily for Linux
   - Better tested on Linux
   - More features available

2. **Easier Installation**
   - Package managers handle dependencies
   - No manual driver installation
   - Fewer compatibility issues

3. **Better Debugging**
   - More diagnostic tools available
   - Better error messages
   - Easier to troubleshoot

### Stability Advantages

1. **Fewer USB Issues**
   - Linux USB stack is more robust
   - Better handling of high-bandwidth devices
   - Fewer "device busy" errors

2. **No Driver Conflicts**
   - No need for Zadig driver replacement
   - Automatic device detection
   - Fewer permission issues

---

## Next Steps

After successful installation:

1. ✅ Test offline decoder: `python src/droneid_receiver_offline.py -i samples/mini2_sm`
2. ✅ Test hardware: `python src/diagnose_receiver.py`
3. ✅ Run live receiver: `python src/droneid_receiver_live.py --gain 55`
4. ✅ Read documentation: `SYSTEM_OVERVIEW.md`
5. ✅ Consider performance tuning (see above)

---

## Getting Help

If you encounter issues:

1. **Check this troubleshooting section**
2. **Run diagnostics:** `python src/diagnose_receiver.py`
3. **Check GitHub Issues:** https://github.com/Skeletoskull/DroneSecurity/issues
4. **GNU Radio Help:** https://wiki.gnuradio.org/
5. **UHD Help:** https://files.ettus.com/manual/

---

**Installation complete! Linux provides the best performance for SDR applications.** 🐧
