# Drone-ID Receiver for DJI OcuSync 2.0 - Windows Port

> **🔱 This is a Windows-compatible fork** of [RUB-SysSec/DroneSecurity](https://github.com/RUB-SysSec/DroneSecurity)  
> **📄 Original Paper:** [Drone Security and the Mysterious Case of DJI's DroneID (NDSS 2023)](https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf)  
> **👥 Original Authors:** Nico Schiller, Merlin Chlosta, Moritz Schloegel, et al. (Ruhr University Bochum)

---

## 🎯 What's New in This Fork

This fork adds **Windows support** and **BladeRF A4 hardware** compatibility to the original Linux/USRP implementation:

### Hardware Support
- ✅ **BladeRF A4** - Nuand BladeRF A4 / 2.0 micro xA4 (Windows & Linux)
- ✅ **USRP B205-mini** - Original Ettus USRP support maintained (Linux)
- ✅ **GNU Radio osmosdr** - Hardware abstraction for multiple SDRs

### Platform Support
- ✅ **Windows 10/11** - Full native Windows support
- ✅ **Linux** - Original Linux support maintained
- ✅ **Cross-platform paths** - Windows-compatible file handling

### Performance Improvements
- ⚡ **Faster STFT** - Optimized packet detection (33% faster)
- ⚡ **Early exit** - Stop processing after finding packets
- ⚡ **Reduced I/O** - Optional file saving for maximum speed
- ⚡ **Frequency locking** - Automatic lock to active frequencies

### Features
- 📊 **JSON output** - Structured telemetry with timestamps
- 🎯 **Frequency scanner** - Intelligent frequency hopping with locking
- 📝 **Comprehensive docs** - Detailed system overview and troubleshooting
- 🧪 **Test suite** - Property-based testing with pytest + hypothesis

### Tested Configuration
- **Hardware:** BladeRF A4, BladeRF 2.0 micro xA4
- **OS:** Windows 10/11, Ubuntu 20.04+
- **Drones:** DJI Mini 2, Mavic Air 2, Mavic 2 (legacy mode)
- **Python:** 3.8, 3.9, 3.10, 3.11

---

## 📖 Original Project

This receiver implements the DroneID protocol reverse-engineering from the NDSS 2023 paper:

**"Drone Security and the Mysterious Case of DJI's DroneID"**  
*Nico Schiller, Merlin Chlosta, Moritz Schloegel, Nils Bars, Thorsten Eisenhofer, Tobias Scharnowski, Felix Domke, Lea Schönherr, Thorsten Holz*

The original project provides:
- Complete DroneID protocol specification
- OFDM demodulation and QPSK decoding
- Zadoff-Chu sequence detection
- Turbo decoder implementation
- Sample captures for testing

**Original Repository:** https://github.com/RUB-SysSec/DroneSecurity

---

## 📚 Installation Guides

**Choose your platform:**

- **[Windows Installation Guide](INSTALLATION_GUIDE_WINDOWS.md)** - Complete setup for Windows 10/11
  - Python, GNU Radio, BladeRF drivers
  - Step-by-step with troubleshooting
  - ~45-60 minutes

- **[Linux Installation Guide](INSTALLATION_GUIDE_LINUX.md)** - Complete setup for Ubuntu/Debian
  - Python, GNU Radio, UHD/BladeRF
  - Performance tuning tips
  - ~20-30 minutes

- **[Platform Comparison](PLATFORM_COMPARISON.md)** - Windows vs Linux technical analysis
  - Why Linux performs better
  - USB performance differences
  - Sample drop explanations
  - Optimization recommendations

## 🚀 Quick Start

### Windows (Quick)

```powershell
# 1. Install Python 3.11 from python.org
# 2. Install GNU Radio (Radioconda recommended)
# 3. Install BladeRF drivers with Zadig

# Clone and setup
git clone https://github.com/Skeletoskull/DroneSecurity.git
cd DroneSecurity
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run receiver
python src\droneid_receiver_live.py --gain 55
```

**⚠️ For detailed instructions, see [INSTALLATION_GUIDE_WINDOWS.md](INSTALLATION_GUIDE_WINDOWS.md)**

### Linux (Quick)

```bash
# Install dependencies
sudo apt install python3 python3-pip gnuradio gr-osmosdr bladerf

# Clone and setup
git clone https://github.com/Skeletoskull/DroneSecurity.git
cd DroneSecurity
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run receiver
python src/droneid_receiver_live.py --gain 55
```

**⚠️ For detailed instructions, see [INSTALLATION_GUIDE_LINUX.md](INSTALLATION_GUIDE_LINUX.md)**

### Test with Sample Files (No Hardware)

```bash
# Works on both Windows and Linux
python src/droneid_receiver_offline.py -i samples/mini2_sm
```

---

## 📚 Documentation

- **[SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)** - Complete system architecture and signal flow
- **[DJI_DroneID_Live_Receiver_Pipeline.md](DJI_DroneID_Live_Receiver_Pipeline.md)** - Processing pipeline details
- **[Original README](#)** - See below for original project documentation

---

## 🤝 Contributing

Contributions are welcome! This fork aims to:
1. Maintain compatibility with the original project
2. Add Windows/BladeRF support without breaking Linux/USRP
3. Improve performance while preserving accuracy
4. Keep code well-documented and tested

### Submitting Changes

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project inherits the **AGPL-3.0** license from the original RUB-SysSec/DroneSecurity project.

**Key requirements:**
- Source code must be provided to users
- Modifications must be disclosed
- Derivative works must use the same license
- Network use constitutes distribution

See [LICENSE](LICENSE) for full details.

---

## 🙏 Acknowledgments

- **Original Authors:** RUB-SysSec team at Ruhr University Bochum
- **Paper:** NDSS 2023 - "Drone Security and the Mysterious Case of DJI's DroneID"
- **Inspiration:** [proto17/dji_droneid](https://github.com/proto17/dji_droneid) - Parallel implementation

---

## ⚠️ Disclaimer

This software is provided for **research and educational purposes only**. The authors and contributors:
- Do not encourage or condone unauthorized drone tracking
- Are not responsible for misuse of this software
- Recommend compliance with local privacy and aviation laws
- Provide this as an academic artifact for reproducibility

---

# Original README Content

[Your existing README content continues below...]
