# Setting Up Your GitHub Fork

## Step 1: Fork the Original Repository

1. Go to: https://github.com/RUB-SysSec/DroneSecurity
2. Click the "Fork" button in the top right
3. Select your account (Skeletoskull) as the destination

## Step 2: Clone Your Fork Locally

```bash
git clone https://github.com/Skeletoskull/DroneSecurity.git
cd DroneSecurity
```

## Step 3: Add Your Windows-Adapted Code

Since you already have the modified code, you'll need to:

```bash
# Add the original repo as upstream (for future updates)
git remote add upstream https://github.com/RUB-SysSec/DroneSecurity.git

# Create a new branch for your Windows port
git checkout -b windows-bladerf-support

# Copy your modified files over the cloned repo
# (You can do this manually or use the commands below)

# Stage all changes
git add .

# Commit with a descriptive message
git commit -m "Add Windows support with BladeRF A4

- Add BladeRF A4 SDR support using GNU Radio osmosdr
- Implement Windows-compatible path handling
- Add frequency scanner with locking mechanism
- Optimize signal processing (faster STFT, early exit)
- Add JSON output format with timestamps
- Add comprehensive system documentation
- Update README with Windows setup instructions
- Add performance optimizations for real-time processing

Tested on Windows 10/11 with BladeRF A4 and Python 3.8+"

# Push to your fork
git push origin windows-bladerf-support
```

## Step 4: Update README to Reflect Fork Status

Add a section at the top of README.md:

```markdown
# Windows Port with BladeRF A4 Support

> **Note:** This is a Windows-compatible fork of [RUB-SysSec/DroneSecurity](https://github.com/RUB-SysSec/DroneSecurity) 
> with added support for BladeRF A4 SDR hardware and Windows operating systems.
>
> **Original Paper:** [Drone Security and the Mysterious Case of DJI's DroneID (NDSS 2023)](https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf)

## Key Differences from Original

- ✅ **Windows Support** - Full Windows 10/11 compatibility
- ✅ **BladeRF A4** - Support for Nuand BladeRF A4 SDR (in addition to USRP)
- ✅ **GNU Radio osmosdr** - Hardware abstraction layer for multiple SDRs
- ✅ **Performance Optimizations** - Faster processing with early exit and reduced I/O
- ✅ **JSON Output** - Structured output format with timestamps
- ✅ **Frequency Locking** - Automatic frequency locking for continuous monitoring

[Rest of your existing README content...]
```

## Step 5: Create a Pull Request (Optional)

If you want to contribute your Windows support back to the original project:

1. Go to your fork on GitHub
2. Click "Pull Request"
3. Select your `windows-bladerf-support` branch
4. Write a description of your changes
5. Submit the PR

The original authors may or may not accept it, but it's good practice to offer!

## Step 6: Maintain Your Fork

To keep your fork updated with upstream changes:

```bash
# Fetch upstream changes
git fetch upstream

# Merge upstream main into your branch
git checkout windows-bladerf-support
git merge upstream/main

# Resolve any conflicts
# Then push to your fork
git push origin windows-bladerf-support
```

## Alternative: Independent Repository

If you prefer NOT to fork (though I don't recommend this):

1. Create a new repo: `DroneSecurity-Windows`
2. Add clear attribution in README:
   ```markdown
   # DroneSecurity - Windows Port
   
   This project is based on [RUB-SysSec/DroneSecurity](https://github.com/RUB-SysSec/DroneSecurity)
   and adds Windows support with BladeRF A4 hardware.
   
   **Original Authors:** Nico Schiller, Merlin Chlosta, et al. (NDSS 2023)
   **License:** AGPL-3.0 (inherited from original)
   ```
3. Keep the original LICENSE file
4. Add your modifications

## Important: License Compliance

The original project is **AGPL-3.0** licensed, which means:

- ✅ You MUST keep the same license
- ✅ You MUST provide source code
- ✅ You MUST attribute the original authors
- ✅ You MUST disclose your changes
- ✅ Network use = distribution (must provide source to users)

Your fork/derivative work must also be AGPL-3.0.
