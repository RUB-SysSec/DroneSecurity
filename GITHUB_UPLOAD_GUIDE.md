# GitHub Upload Guide for Your DroneSecurity Windows Port

## Summary

You have a **Windows-adapted fork** of the RUB-SysSec DroneSecurity project with significant improvements:

### Your Contributions
1. **BladeRF A4 support** - Added Windows-compatible SDR hardware support
2. **GNU Radio integration** - Hardware abstraction via osmosdr
3. **Windows compatibility** - Path handling, file I/O, signal handlers
4. **Performance optimizations** - 33% faster processing
5. **JSON output** - Structured telemetry format
6. **Frequency locking** - Intelligent frequency management
7. **Comprehensive documentation** - System overview and troubleshooting

### Original Project
- **Repository:** https://github.com/RUB-SysSec/DroneSecurity
- **Paper:** NDSS 2023 - "Drone Security and the Mysterious Case of DJI's DroneID"
- **Authors:** Nico Schiller, Merlin Chlosta, et al. (Ruhr University Bochum)
- **License:** AGPL-3.0

---

## Recommendation: FORK THE ORIGINAL

**I strongly recommend forking** for these reasons:

### ✅ Pros of Forking
- **Proper attribution** - Shows respect for academic research
- **Clear lineage** - Users see the relationship between projects
- **Easier collaboration** - Can contribute back upstream
- **Academic integrity** - Maintains research provenance
- **Discoverability** - Your work becomes visible from original repo
- **License compliance** - AGPL-3.0 requires attribution

### ❌ Cons of Independent Repo
- Harder to track relationship to original
- May appear to claim original work
- Misses opportunity for upstream contribution
- Less discoverable by the community

---

## Step-by-Step: Fork and Upload

### 1. Fork on GitHub

```
1. Go to: https://github.com/RUB-SysSec/DroneSecurity
2. Click "Fork" button (top right)
3. Select "Skeletoskull" as destination
4. Wait for fork to complete
```

### 2. Clone Your Fork

```bash
git clone https://github.com/Skeletoskull/DroneSecurity.git
cd DroneSecurity
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/RUB-SysSec/DroneSecurity.git
git remote -v
# Should show:
# origin    https://github.com/Skeletoskull/DroneSecurity.git (fetch)
# origin    https://github.com/Skeletoskull/DroneSecurity.git (push)
# upstream  https://github.com/RUB-SysSec/DroneSecurity.git (fetch)
# upstream  https://github.com/RUB-SysSec/DroneSecurity.git (push)
```

### 4. Create Feature Branch

```bash
git checkout -b windows-bladerf-support
```

### 5. Copy Your Modified Files

**Option A: Manual Copy**
- Copy all your modified files from your current directory
- Overwrite the cloned files

**Option B: Using Commands** (if you're in your current project directory)
```bash
# Assuming you're in your current project directory
# and the fork is in ../DroneSecurity

# Copy all source files
cp -r src/* ../DroneSecurity/src/
cp -r tests/* ../DroneSecurity/tests/
cp requirements.txt ../DroneSecurity/
cp SYSTEM_OVERVIEW.md ../DroneSecurity/
cp DJI_DroneID_Live_Receiver_Pipeline.md ../DroneSecurity/

# Then go to the fork directory
cd ../DroneSecurity
```

### 6. Update README

Add the fork header to the top of README.md:

```bash
# Open README.md in your editor
# Add the content from README_FORK_HEADER.md to the top
# Keep the original content below
```

### 7. Stage and Commit Changes

```bash
git add .
git status  # Review what will be committed

git commit -m "Add Windows support with BladeRF A4

Major changes:
- Add BladeRF A4 SDR support using GNU Radio osmosdr
- Implement Windows-compatible path handling (path_utils.py)
- Add frequency scanner with intelligent locking mechanism
- Optimize signal processing (faster STFT, early exit, reduced I/O)
- Add JSON output format with timestamps and telemetry
- Add comprehensive system documentation (SYSTEM_OVERVIEW.md)
- Update README with Windows setup instructions
- Add performance optimizations for real-time processing
- Add test suite with pytest and hypothesis

Hardware tested:
- BladeRF A4, BladeRF 2.0 micro xA4
- Windows 10/11, Ubuntu 20.04+
- DJI Mini 2, Mavic Air 2, Mavic 2 (legacy mode)

Performance improvements:
- 33% faster frequency scanning (1.4s vs 2.1s per frequency)
- Early exit after finding packets
- Optional file saving for maximum speed
- Optimized STFT parameters (noverlap=0, smaller nfft)

Maintains backward compatibility with original Linux/USRP implementation."
```

### 8. Push to Your Fork

```bash
git push origin windows-bladerf-support
```

### 9. Create Pull Request (Optional)

If you want to contribute back to the original project:

```
1. Go to: https://github.com/Skeletoskull/DroneSecurity
2. Click "Pull Request" button
3. Select: base: RUB-SysSec/DroneSecurity main ← head: Skeletoskull/DroneSecurity windows-bladerf-support
4. Title: "Add Windows support with BladeRF A4 hardware"
5. Description: Explain your changes, testing, and motivation
6. Click "Create Pull Request"
```

**Note:** The original authors may or may not accept it, but it's good practice to offer!

### 10. Set Default Branch (Optional)

If you want your Windows branch to be the default:

```
1. Go to: https://github.com/Skeletoskull/DroneSecurity/settings
2. Click "Branches" in left sidebar
3. Change default branch to "windows-bladerf-support"
4. Confirm the change
```

---

## Alternative: Independent Repository

If you prefer NOT to fork (though I don't recommend this):

### 1. Create New Repository

```
1. Go to: https://github.com/new
2. Name: "DroneSecurity-Windows" or "DJI-DroneID-Windows"
3. Description: "Windows port of RUB-SysSec/DroneSecurity with BladeRF A4 support"
4. Public repository
5. Do NOT initialize with README (you have one)
6. Click "Create repository"
```

### 2. Push Your Code

```bash
cd your-current-project-directory
git init
git add .
git commit -m "Initial commit: Windows port of DroneSecurity"
git branch -M main
git remote add origin https://github.com/Skeletoskull/DroneSecurity-Windows.git
git push -u origin main
```

### 3. Add Clear Attribution

**CRITICAL:** Add this to the top of your README:

```markdown
# DroneSecurity - Windows Port with BladeRF A4

> **⚠️ IMPORTANT:** This project is based on [RUB-SysSec/DroneSecurity](https://github.com/RUB-SysSec/DroneSecurity)
> 
> **Original Paper:** [Drone Security and the Mysterious Case of DJI's DroneID (NDSS 2023)](https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf)
> 
> **Original Authors:** Nico Schiller, Merlin Chlosta, Moritz Schloegel, Nils Bars, Thorsten Eisenhofer, Tobias Scharnowski, Felix Domke, Lea Schönherr, Thorsten Holz
> 
> **License:** AGPL-3.0 (inherited from original project)
> 
> This is a derivative work that adds Windows support and BladeRF A4 hardware compatibility.
```

---

## License Compliance (CRITICAL)

The original project is **AGPL-3.0** licensed. You MUST:

### ✅ Required Actions
1. **Keep AGPL-3.0 license** - Your fork must use the same license
2. **Attribute original authors** - Credit RUB-SysSec team
3. **Disclose source code** - Provide source to all users (you're doing this)
4. **Document changes** - List your modifications (in README or CHANGELOG)
5. **Preserve copyright notices** - Keep original license headers

### ❌ Prohibited Actions
- Cannot change to a different license (MIT, Apache, etc.)
- Cannot remove attribution to original authors
- Cannot make it proprietary/closed-source
- Cannot use it in closed-source network services without providing source

### 📝 What AGPL-3.0 Means
- **Network use = distribution** - If someone uses your receiver over a network, you must provide source
- **Copyleft** - Derivative works must also be AGPL-3.0
- **Patent grant** - Contributors grant patent rights
- **No warranty** - Software provided "as-is"

---

## Recommended Repository Structure

```
DroneSecurity/  (or your fork name)
├── README.md                              # Updated with fork header
├── LICENSE                                # AGPL-3.0 (keep original)
├── SYSTEM_OVERVIEW.md                     # Your comprehensive docs
├── DJI_DroneID_Live_Receiver_Pipeline.md  # Your pipeline docs
├── requirements.txt                       # Updated dependencies
├── .gitignore                            # Keep original
├── src/
│   ├── droneid_receiver_live.py          # Your Windows-compatible version
│   ├── bladerf_receiver.py               # Your BladeRF implementation
│   ├── frequency_scanner.py              # Your frequency management
│   ├── path_utils.py                     # Your Windows path handling
│   ├── config.py                         # Your configuration
│   └── [other original files]
├── tests/
│   ├── test_bladerf_receiver.py          # Your tests
│   ├── test_frequency_scanner.py
│   └── [other tests]
├── samples/
│   ├── mini2_sm                          # Original samples
│   └── mavic_air_2
└── img/
    └── [original images]
```

---

## After Upload: Repository Settings

### 1. Add Topics (Tags)

```
Settings → General → Topics
Add: sdr, dji, droneid, bladerf, gnuradio, windows, ofdm, qpsk, drone-security
```

### 2. Add Description

```
Windows port of DroneSecurity with BladeRF A4 support - DJI DroneID receiver (NDSS 2023)
```

### 3. Add Website

```
https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf
```

### 4. Enable Issues

```
Settings → General → Features → ✅ Issues
```

### 5. Add README Badges (Optional)

Add to top of README:

```markdown
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)]()
[![Hardware](https://img.shields.io/badge/hardware-BladeRF%20A4-orange.svg)](https://www.nuand.com/)
```

---

## Maintaining Your Fork

### Keep Updated with Upstream

```bash
# Fetch upstream changes
git fetch upstream

# Merge into your branch
git checkout windows-bladerf-support
git merge upstream/main

# Resolve conflicts if any
# Then push
git push origin windows-bladerf-support
```

### Sync Regularly

```bash
# Create a script: sync-upstream.sh
#!/bin/bash
git fetch upstream
git checkout windows-bladerf-support
git merge upstream/main
git push origin windows-bladerf-support
```

---

## Summary: What to Do

### Recommended Path (Fork)

1. ✅ Fork RUB-SysSec/DroneSecurity on GitHub
2. ✅ Clone your fork locally
3. ✅ Create `windows-bladerf-support` branch
4. ✅ Copy your modified files
5. ✅ Update README with fork header
6. ✅ Commit with detailed message
7. ✅ Push to your fork
8. ✅ (Optional) Create PR to upstream
9. ✅ Add topics and description
10. ✅ Share with community!

### Key Points

- **Attribution is critical** - Always credit original authors
- **License compliance** - Must stay AGPL-3.0
- **Document changes** - Explain what you modified
- **Test thoroughly** - Ensure Windows compatibility
- **Maintain compatibility** - Don't break Linux/USRP support

---

## Questions?

If you have questions about:
- **Forking process** - Check GitHub's fork documentation
- **License compliance** - Read AGPL-3.0 FAQ
- **Git commands** - See Git documentation
- **Contributing upstream** - Contact original authors

---

## Final Checklist

Before uploading:

- [ ] Decided: Fork or independent repo?
- [ ] Updated README with attribution
- [ ] Kept original LICENSE file
- [ ] Documented your changes
- [ ] Tested on Windows
- [ ] Tested on Linux (if possible)
- [ ] Added comprehensive documentation
- [ ] Wrote clear commit messages
- [ ] Added topics/tags to repo
- [ ] Set repository description
- [ ] Enabled issues for feedback

---

**Good luck with your upload! Your Windows port is a valuable contribution to the drone security research community.** 🚀
