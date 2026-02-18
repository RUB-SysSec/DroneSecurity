# Frequently Asked Questions (FAQ)

## General Questions

### What is this project?

This is a Windows-compatible fork of the RUB-SysSec DroneSecurity project, which implements a receiver for DJI's proprietary DroneID protocol. It allows you to receive and decode telemetry data transmitted by DJI drones.

### Is this legal?

**Yes**, receiving radio signals is generally legal in most jurisdictions. However:
- ⚠️ **Check local laws** - Radio regulations vary by country
- ⚠️ **Privacy concerns** - Be aware of privacy implications
- ⚠️ **Research use** - This is intended for academic/research purposes
- ⚠️ **No malicious use** - Do not use for unauthorized tracking or harassment

**Disclaimer:** The authors are not responsible for misuse of this software.

### What's the difference between this and the original?

**This fork adds:**
- Windows 10/11 support
- BladeRF A4 hardware support
- GNU Radio osmosdr integration
- Performance optimizations (33% faster)
- JSON output format
- Frequency locking mechanism
- Comprehensive documentation

**Original project:**
- Linux only
- USRP B205-mini only
- UHD driver
- Basic output format

### Is this the same as "Remote ID"?

**No!** This is different:

**DJI DroneID (this project):**
- Proprietary DJI protocol
- Uses OFDM/QPSK modulation
- Requires SDR to receive
- 2.4/5.8 GHz bands
- DJI drones only

**Remote ID (standard):**
- International standard (ASTM F3411, EN 4709)
- Uses WiFi or Bluetooth
- Can receive with smartphone
- 2.4/5 GHz WiFi bands
- All drone manufacturers

---

## Hardware Questions

### What SDR hardware do I need?

**Windows:**
- ✅ BladeRF A4
- ✅ BladeRF 2.0 micro xA4
- ❌ USRP (not supported on Windows)

**Linux:**
- ✅ BladeRF A4
- ✅ BladeRF 2.0 micro xA4
- ✅ Ettus USRP B205-mini (original hardware)
- ⚠️ Other SDRs may work but are untested

### Can I use RTL-SDR / HackRF / LimeSDR?

**No**, these SDRs are not suitable:

**RTL-SDR:**
- Max sample rate: 2.4 MHz (need 50 MHz)
- 8-bit ADC (need 12-bit)
- No transmit capability
- Too limited for this application

**HackRF One:**
- Max sample rate: 20 MHz (need 50 MHz)
- 8-bit ADC (need 12-bit)
- May work with reduced performance (untested)

**LimeSDR:**
- Sufficient sample rate (61.44 MHz)
- 12-bit ADC
- May work but untested
- No official support

**Why BladeRF/USRP?**
- 50+ MHz sample rate
- 12-bit ADC
- Proven to work
- Good USB 3.0 performance

### Do I need an antenna?

**Yes!** The SDR comes with antennas, but:

**Included antennas:**
- Usually adequate for testing
- Range: 50-200 meters

**Better antennas:**
- Directional antenna (Yagi): 500+ meters
- Omnidirectional (discone): 360° coverage
- Frequency: 2.4 GHz and/or 5.8 GHz

**Recommendation:** Start with included antenna, upgrade if needed.

### What USB port should I use?

**Critical:** Use **USB 3.0** port (blue port)!

**Why:**
- 50 MHz sample rate = 200 MB/s bandwidth
- USB 2.0 max: 40 MB/s (too slow!)
- USB 3.0 max: 400 MB/s (sufficient)

**Tips:**
- Use motherboard USB port (not front panel)
- Avoid USB hubs (even powered ones)
- Prefer Intel USB controllers
- Check if port is shared with other devices

---

## Software Questions

### What operating system should I use?

**For best performance:** Linux (Ubuntu 22.04 recommended)

**For convenience:** Windows 10/11 works but with limitations

**See:** [PLATFORM_COMPARISON.md](PLATFORM_COMPARISON.md) for detailed comparison.

### What Python version do I need?

**Supported:** Python 3.8, 3.9, 3.10, 3.11

**Recommended:** Python 3.11 (best performance)

**Not supported:** Python 3.12+ (some dependencies may not work)

**Check version:**
```bash
python --version
```

### Do I need GNU Radio?

**Yes!** GNU Radio is **required** for SDR hardware abstraction.

**Why:**
- Provides osmosdr source block
- Handles USB streaming
- Converts sample formats
- Manages device configuration

**Without GNU Radio:**
- You'd need to write low-level SDR code
- Platform-specific for each SDR
- Much more complex

**Installation:**
- Windows: Radioconda (easiest)
- Linux: `sudo apt install gnuradio gr-osmosdr`

### Can I run this without an SDR?

**Yes!** You can test with sample files:

```bash
python src/droneid_receiver_offline.py -i samples/mini2_sm
```

This decodes pre-recorded samples without hardware.

---

## Usage Questions

### How do I know if it's working?

**Signs it's working:**
1. No error messages on startup
2. "Scanning: X MHz" messages appear
3. When drone is nearby, JSON output appears
4. CRC validation passes (✅)

**Signs it's not working:**
1. "Device not found" error
2. "USB communication error"
3. No output when drone is nearby
4. Many CRC errors

**Test:**
```bash
# Test with sample file (no hardware needed)
python src/droneid_receiver_offline.py -i samples/mini2_sm
# Should show decoded JSON output
```

### Why am I not detecting any drones?

**Checklist:**
1. ✅ Drone is powered on and connected to controller
2. ✅ Drone is within range (50-200m with stock antenna)
3. ✅ Antenna is connected to SDR
4. ✅ Using correct gain setting (try 55-60)
5. ✅ Drone has DroneID enabled (most DJI drones do)
6. ✅ Not using legacy drone without --legacy flag

**Try:**
```bash
# Increase gain
python src/droneid_receiver_live.py --gain 60

# Try legacy mode
python src/droneid_receiver_live.py --gain 60 --legacy

# Enable verbose output
python src/droneid_receiver_live.py --gain 60 --verbose
```

### What does "CRC error" mean?

**CRC (Cyclic Redundancy Check)** validates packet integrity.

**CRC error means:**
- Packet was decoded but corrupted
- Weak signal
- Interference
- Sample drops

**Solutions:**
1. Increase gain: `--gain 60`
2. Move antenna closer to drone
3. Check antenna orientation
4. Reduce interference (turn off WiFi, Bluetooth)
5. Use USB 3.0 port
6. Use Linux (better USB performance)

**Some CRC errors are normal** - aim for > 80% success rate.

### What gain setting should I use?

**Gain guide:**
- **0** - Automatic gain control (AGC)
- **30** - Default, low noise
- **40** - Weak signals
- **55** - Recommended starting point
- **60** - Maximum, high noise

**Recommendation:**
1. Start with 55
2. If no detection, try 60
3. If too much noise, try 40
4. If still issues, try AGC (0)

**Trade-off:**
- Higher gain = more range but more noise
- Lower gain = less noise but less range

### How close does the drone need to be?

**Range depends on:**
- Antenna quality
- Gain setting
- Interference level
- Drone transmit power

**Typical ranges:**
- Stock antenna: 50-200 meters
- Directional antenna: 500+ meters
- Optimal conditions: 1+ km

**Start with:** 10-50 meters for testing

### Can I track multiple drones simultaneously?

**No**, the current implementation tracks one drone at a time.

**Why:**
- Frequency locking mechanism
- Single processing pipeline
- Bandwidth limitations

**Workaround:**
- Run multiple instances on different frequencies
- Use multiple SDRs
- Modify code to support multiple drones (advanced)

---

## Performance Questions

### Why is my CPU usage so high?

**Normal CPU usage:** 60-80%

**Reasons:**
- Real-time signal processing at 50 MHz
- STFT analysis
- OFDM demodulation
- QPSK decoding
- Multiple worker processes

**Reduce CPU usage:**
```bash
# Reduce workers
python src/droneid_receiver_live.py --workers 1

# Shorter duration
python src/droneid_receiver_live.py --duration 0.8

# 2.4 GHz only
python src/droneid_receiver_live.py --band-2-4-only
```

### Why am I getting sample drops?

**Sample drops** occur when the computer can't keep up with the SDR.

**Common causes:**
1. ❌ Using USB 2.0 port (use USB 3.0!)
2. ❌ USB power management enabled
3. ❌ Background applications running
4. ❌ Insufficient CPU power
5. ❌ Using Windows (Linux performs better)

**Solutions:**
1. ✅ Use USB 3.0 port (blue port)
2. ✅ Disable USB power management
3. ✅ Close background applications
4. ✅ Reduce workers: `--workers 1`
5. ✅ Use Linux

**See:** [PLATFORM_COMPARISON.md](PLATFORM_COMPARISON.md) for detailed explanation.

### Why is Linux faster than Windows?

**Linux advantages:**
- Native USB support (no driver layers)
- Better real-time scheduling
- Lower latency (1-2ms vs 5-10ms)
- Better memory management
- Fewer background processes

**Windows disadvantages:**
- Extra driver layers (WinUSB)
- Limited real-time support
- Higher latency
- More background processes

**Result:** Linux has ~33% better performance and fewer sample drops.

**See:** [PLATFORM_COMPARISON.md](PLATFORM_COMPARISON.md) for full analysis.

---

## Troubleshooting Questions

### "Device not found" error

**Windows:**
1. Check BladeRF is connected to USB 3.0 port
2. Verify Zadig driver installation
3. Try different USB port
4. Restart computer
5. Check Device Manager for "Unknown Device"

**Linux:**
1. Check USB connection: `lsusb | grep -i nuand`
2. Check permissions: `ls -l /dev/bus/usb/*/*`
3. Add udev rules (see installation guide)
4. Add user to plugdev group
5. Log out and log back in

### "ImportError: No module named 'osmosdr'"

**Cause:** GNU Radio not installed or not in PATH

**Windows:**
```powershell
# Install Radioconda
# Or add GNU Radio to PATH
```

**Linux:**
```bash
sudo apt install gr-osmosdr
```

### "Permission denied" error

**Linux only:**

```bash
# Add user to plugdev group
sudo usermod -a -G plugdev $USER

# Add udev rules
sudo wget https://www.nuand.com/bladeRF.rules -O /etc/udev/rules.d/88-nuand-bladerf1.rules
sudo udevadm control --reload-rules

# Log out and log back in
```

### "USB communication error"

**Causes:**
- USB 2.0 port (need USB 3.0)
- USB hub (use direct connection)
- USB cable issue
- USB power management
- Device busy (another app using SDR)

**Solutions:**
1. Use USB 3.0 port (blue port)
2. Avoid USB hubs
3. Try different USB cable
4. Disable USB power management
5. Close other SDR applications (SDR#, GQRX, etc.)
6. Restart computer

---

## Advanced Questions

### Can I modify the code?

**Yes!** This is open-source (AGPL-3.0 license).

**Requirements:**
- Keep AGPL-3.0 license
- Attribute original authors
- Disclose source code
- Document changes

**See:** [LICENSE](LICENSE) for details.

### Can I use this for commercial purposes?

**Yes**, but with restrictions:

**AGPL-3.0 requirements:**
- Provide source code to users
- Keep same license
- Attribute original authors
- If used over network, provide source to network users

**Not allowed:**
- Make it proprietary/closed-source
- Remove attribution
- Change license

### How can I contribute?

**Ways to contribute:**
1. Report bugs (GitHub Issues)
2. Submit pull requests
3. Improve documentation
4. Test on different hardware
5. Add support for more drones
6. Optimize performance

**See:** [CONTRIBUTING.md](CONTRIBUTING.md) (if exists)

### Can I add support for other SDRs?

**Yes!** You'd need to:

1. Create new receiver class (like `BladeRFReceiver`)
2. Implement same interface:
   - `set_frequency()`
   - `set_gain()`
   - `receive_samples()`
3. Update `droneid_receiver_live.py` to use new receiver
4. Test thoroughly
5. Submit pull request

**Example SDRs to add:**
- LimeSDR
- PlutoSDR
- USRP on Windows (via UHD)

### How does the frequency locking work?

**Mechanism:**
1. Scan all frequencies in round-robin
2. When DroneID detected, lock to that frequency
3. Continue monitoring locked frequency
4. After 10 consecutive empty scans, unlock
5. Resume scanning all frequencies

**Benefits:**
- Don't miss packets while scanning
- Faster updates when drone is active
- Automatic resumption when drone moves

**See:** `src/frequency_scanner.py` for implementation.

### What's the detection range?

**Factors:**
- Antenna quality
- Gain setting
- Interference level
- Drone transmit power
- Line of sight

**Typical ranges:**
- Stock antenna: 50-200m
- Directional antenna: 500m+
- Optimal conditions: 1km+

**DJI transmit power:** ~20 dBm (100 mW)

**Link budget calculation:**
```
Received power = Tx power + Tx antenna gain - Path loss + Rx antenna gain - Rx losses

Example:
20 dBm + 2 dBi - 80 dB + 2 dBi - 3 dB = -59 dBm

At -59 dBm, signal is easily detectable.
```

---

## Comparison Questions

### How does this compare to proto17/dji_droneid?

**proto17/dji_droneid:**
- Parallel implementation
- Developed independently
- Similar approach
- Different codebase

**This project (RUB-SysSec fork):**
- Academic research (NDSS 2023)
- More documentation
- Windows support (this fork)
- More testing

**Both are excellent!** Check out both implementations.

### How does this compare to OpenDroneID?

**OpenDroneID:**
- Standard Remote ID (ASTM F3411)
- WiFi/Bluetooth based
- Works with smartphone
- All drone manufacturers
- Easier to receive

**This project:**
- DJI proprietary DroneID
- OFDM/QPSK based
- Requires SDR
- DJI drones only
- More complex

**Use OpenDroneID for:** Standard Remote ID

**Use this project for:** DJI-specific DroneID

---

## Future Questions

### Will you add support for X feature?

**Planned features:**
- GPU acceleration
- Real-time visualization
- Database logging
- Web interface
- Multi-SDR support

**See:** [CHANGELOG_WINDOWS_PORT.md](CHANGELOG_WINDOWS_PORT.md) for roadmap.

### Will you support other drone manufacturers?

**No**, this project is specific to DJI's proprietary protocol.

**For other manufacturers:**
- Use OpenDroneID (standard Remote ID)
- Each manufacturer has different protocols
- Would require separate implementations

### Will you add a GUI?

**Maybe!** Challenges:
- matplotlib GUI has issues on Windows
- Would need cross-platform GUI framework
- Adds complexity
- Current CLI works well

**Workaround:** Use offline decoder with `--gui` flag on Linux.

---

## Getting Help

### Where can I get help?

1. **Read documentation:**
   - [README.md](README.md)
   - [INSTALLATION_GUIDE_WINDOWS.md](INSTALLATION_GUIDE_WINDOWS.md)
   - [INSTALLATION_GUIDE_LINUX.md](INSTALLATION_GUIDE_LINUX.md)
   - [PLATFORM_COMPARISON.md](PLATFORM_COMPARISON.md)
   - [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)
   - [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

2. **Run diagnostics:**
   ```bash
   python src/diagnose_receiver.py
   ```

3. **Check GitHub Issues:**
   - https://github.com/Skeletoskull/DroneSecurity/issues

4. **Read original paper:**
   - https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf

5. **Community resources:**
   - GNU Radio mailing list
   - BladeRF forums
   - Reddit: r/RTLSDR, r/GNURadio

### How do I report a bug?

**GitHub Issues:** https://github.com/Skeletoskull/DroneSecurity/issues

**Include:**
1. Operating system and version
2. Python version
3. GNU Radio version
4. SDR hardware
5. Complete error message
6. Steps to reproduce
7. Output of `python src/diagnose_receiver.py`

### How do I request a feature?

**GitHub Issues:** https://github.com/Skeletoskull/DroneSecurity/issues

**Label:** "enhancement"

**Include:**
1. Clear description of feature
2. Use case / motivation
3. Expected behavior
4. Willingness to contribute

---

**Still have questions? Open a GitHub Issue!** 💬
