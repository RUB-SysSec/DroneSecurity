# Project Structure

This document describes the organization of the DroneSecurity Windows Port repository.

## Directory Layout

```
DroneSecurity/
├── src/                          # Source code
│   ├── droneid_receiver_live.py  # Live receiver (main entry point)
│   ├── droneid_receiver_offline.py # Offline decoder
│   ├── bladerf_receiver.py       # BladeRF hardware interface
│   ├── frequency_scanner.py      # Frequency hopping logic
│   ├── config.py                 # Configuration dataclasses
│   ├── path_utils.py             # Cross-platform path handling
│   ├── SpectrumCapture.py        # Packet detection
│   ├── Packet.py                 # OFDM demodulation
│   ├── qpsk.py                   # QPSK decoder
│   ├── droneid_packet.py         # DroneID packet parser
│   ├── packetizer.py             # Time-domain packet detection
│   ├── helpers.py                # Signal processing utilities
│   ├── goldgen.py                # Gold sequence generator
│   ├── zcsequence.py             # Zadoff-Chu sequences
│   ├── gui.py                    # Interactive GUI (Linux only)
│   ├── map.py                    # Map plotting utilities
│   └── diagnose_receiver.py      # Hardware diagnostics
│
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest configuration
│   ├── test_bladerf_receiver.py  # Hardware tests
│   ├── test_frequency_scanner.py # Frequency scanner tests
│   ├── test_path_utils.py        # Path handling tests
│   ├── test_cli_arguments.py     # CLI argument tests
│   ├── test_json_output.py       # Output format tests
│   ├── test_signal_processing.py # Signal processing tests
│   ├── test_decoder_parser.py    # Decoder tests
│   └── test_sample_conversion.py # Sample conversion tests
│
├── samples/                      # Sample captures
│   ├── mini2_sm                  # DJI Mini 2 sample
│   └── mavic_air_2               # DJI Mavic Air 2 sample
│
├── img/                          # Documentation images
│   ├── paper_thumbnail.png       # NDSS paper thumbnail
│   ├── pipeline.png              # Processing pipeline diagram
│   ├── inspectrum.png            # Inspectrum screenshot
│   └── result.png                # Decoded output example
│
├── docs/                         # Documentation (root level)
│   ├── README.md                 # Main documentation
│   ├── INSTALLATION_GUIDE_WINDOWS.md
│   ├── INSTALLATION_GUIDE_LINUX.md
│   ├── PLATFORM_COMPARISON.md
│   ├── SYSTEM_OVERVIEW.md
│   ├── DJI_DroneID_Live_Receiver_Pipeline.md
│   ├── QUICK_REFERENCE.md
│   ├── FAQ.md
│   ├── DOCUMENTATION_INDEX.md
│   ├── CHANGELOG_WINDOWS_PORT.md
│   ├── GITHUB_UPLOAD_GUIDE.md
│   ├── FORK_SETUP_INSTRUCTIONS.md
│   ├── SETUP_GIT_AND_GITHUB.md
│   ├── PROJECT_STRUCTURE.md      # This file
│   └── CONTRIBUTING.md
│
├── .gitignore                    # Git ignore rules
├── LICENSE                       # AGPL-3.0 license
└── requirements.txt              # Python dependencies
```

## Core Components

### Live Receiver (`src/droneid_receiver_live.py`)
- Main entry point for real-time reception
- Multi-threaded architecture
- Frequency scanning and locking
- JSON output format

### Offline Decoder (`src/droneid_receiver_offline.py`)
- Decode pre-recorded samples
- No hardware required
- Useful for testing and analysis

### Hardware Interface (`src/bladerf_receiver.py`)
- BladeRF A4 hardware abstraction
- GNU Radio osmosdr integration
- Sample streaming management
- USB 3.0 optimization

### Frequency Scanner (`src/frequency_scanner.py`)
- Frequency hopping logic
- Automatic frequency locking
- 2.4 GHz and 5.8 GHz bands
- Configurable scan patterns

### Signal Processing Pipeline
1. **SpectrumCapture.py** - Packet detection (STFT-based)
2. **Packet.py** - OFDM demodulation and ZC sequence detection
3. **qpsk.py** - QPSK symbol decoding
4. **droneid_packet.py** - DroneID packet parsing

## Documentation Structure

### User Documentation
- **README.md** - Project overview and quick start
- **INSTALLATION_GUIDE_WINDOWS.md** - Windows setup (45-60 min)
- **INSTALLATION_GUIDE_LINUX.md** - Linux setup (20-30 min)
- **QUICK_REFERENCE.md** - Command cheat sheet
- **FAQ.md** - Frequently asked questions

### Technical Documentation
- **PLATFORM_COMPARISON.md** - Windows vs Linux analysis
- **SYSTEM_OVERVIEW.md** - System architecture
- **DJI_DroneID_Live_Receiver_Pipeline.md** - Signal processing pipeline
- **CHANGELOG_WINDOWS_PORT.md** - Change history

### Developer Documentation
- **CONTRIBUTING.md** - Contribution guidelines
- **PROJECT_STRUCTURE.md** - This file
- **GITHUB_UPLOAD_GUIDE.md** - GitHub setup
- **FORK_SETUP_INSTRUCTIONS.md** - Forking workflow

## File Naming Conventions

### Python Files
- **snake_case** for all Python files
- **PascalCase** for class files (Packet.py, SpectrumCapture.py)
- Descriptive names indicating purpose

### Documentation Files
- **UPPERCASE_WITH_UNDERSCORES.md** for major docs
- Clear, descriptive names
- Markdown format (.md)

### Output Files
- **lowercase_with_timestamp** for generated files
- Pattern: `{prefix}_{MMDD}_{HHMM}.{ext}`
- Examples:
  - `decoded_bits_0218_1430.bin`
  - `ext_drone_id_50000000_0218_1430.raw`
  - `receive_test_0218_1430.raw`

## Code Organization

### Module Dependencies
```
droneid_receiver_live.py
├── bladerf_receiver.py
│   └── osmosdr (GNU Radio)
├── frequency_scanner.py
├── config.py
├── path_utils.py
├── SpectrumCapture.py
│   ├── packetizer.py
│   └── helpers.py
├── Packet.py
│   ├── zcsequence.py
│   └── helpers.py
├── qpsk.py
│   └── goldgen.py
└── droneid_packet.py
```

### Configuration Flow
```
Command Line Args
    ↓
argparse
    ↓
ReceiverConfig (config.py)
    ↓
BladeRFReceiver + FrequencyScanner
    ↓
Processing Pipeline
```

## Testing Structure

### Test Organization
- **Unit tests** - Individual component testing
- **Integration tests** - Component interaction testing
- **Property-based tests** - Hypothesis framework
- **Hardware tests** - BladeRF device testing

### Test Naming
- `test_{component}_{function}.py`
- Example: `test_frequency_scanner_locking.py`

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_frequency_scanner.py

# With coverage
pytest --cov=src tests/

# Verbose output
pytest -v
```

## Build and Distribution

### Dependencies
- **requirements.txt** - Python package dependencies
- **GNU Radio** - Installed separately (system package)
- **BladeRF drivers** - Installed separately (Zadig on Windows)

### Virtual Environment
```bash
# Create
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Version Control

### Git Workflow
1. Fork original repository
2. Create feature branch
3. Make changes
4. Commit with descriptive messages
5. Push to fork
6. Create pull request

### Ignored Files (.gitignore)
- Python cache (`__pycache__/`, `*.pyc`)
- Virtual environments (`.venv/`, `venv/`)
- IDE files (`.vscode/`, `.kiro/`, `.idea/`)
- Output files (`*.raw`, `*.bin`)
- Test artifacts (`.pytest_cache/`, `.hypothesis/`)

## Release Process

### Version Numbering
- **Major.Minor.Patch** (Semantic Versioning)
- Example: 2.0.0 (Windows Port)

### Release Checklist
1. Update CHANGELOG_WINDOWS_PORT.md
2. Update version numbers
3. Run full test suite
4. Update documentation
5. Create git tag
6. Push to GitHub
7. Create GitHub release

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## License

This project is licensed under AGPL-3.0. See [LICENSE](LICENSE) for details.

---

**Last Updated:** February 18, 2026  
**Version:** 2.0 (Windows Port)
