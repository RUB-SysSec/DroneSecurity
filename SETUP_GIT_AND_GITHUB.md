# Setting Up Git and GitHub - Quick Guide

## Step 1: Install Git for Windows

### Option A: Download and Install (Recommended)

1. **Download Git:**
   - Go to: https://git-scm.com/download/win
   - Download the latest version (64-bit)
   - File will be named something like: `Git-2.43.0-64-bit.exe`

2. **Install Git:**
   - Run the downloaded installer
   - **Important settings during installation:**
     - ✅ Use default options for most screens
     - ✅ Select "Git from the command line and also from 3rd-party software"
     - ✅ Use "Checkout Windows-style, commit Unix-style line endings"
     - ✅ Use MinTTY (default terminal)
     - ✅ Enable Git Credential Manager

3. **Verify Installation:**
   - Close and reopen your terminal/PowerShell
   - Run: `git --version`
   - Should show: `git version 2.43.0` (or similar)

### Option B: Install via Winget (Windows 11)

```powershell
winget install --id Git.Git -e --source winget
```

### Option C: Install via Chocolatey

```powershell
choco install git
```

---

## Step 2: Configure Git

After installing Git, configure your identity:

```powershell
# Set your name (will appear in commits)
git config --global user.name "Skeletoskull"

# Set your email (use your GitHub email)
git config --global user.email "your-email@example.com"

# Verify configuration
git config --list
```

---

## Step 3: Create GitHub Account (if you don't have one)

1. Go to: https://github.com/signup
2. Username: **Skeletoskull** (or your preferred username)
3. Email: Use a valid email address
4. Password: Create a strong password
5. Verify your email address

---

## Step 4: Set Up GitHub Authentication

### Option A: Personal Access Token (Recommended for Windows)

1. **Generate Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name: "DroneSecurity Windows Port"
   - Expiration: 90 days (or custom)
   - Scopes: Select **repo** (all sub-options)
   - Click "Generate token"
   - **COPY THE TOKEN** - you won't see it again!

2. **Use Token:**
   - When git asks for password, paste the token instead
   - Git Credential Manager will save it for future use

### Option B: SSH Key (Alternative)

```powershell
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Press Enter to accept default location
# Enter a passphrase (optional but recommended)

# Copy public key to clipboard
Get-Content ~/.ssh/id_ed25519.pub | Set-Clipboard

# Add to GitHub:
# 1. Go to: https://github.com/settings/keys
# 2. Click "New SSH key"
# 3. Title: "Windows PC"
# 4. Paste the key
# 5. Click "Add SSH key"
```

---

## Step 5: Fork the Original Repository

1. **Go to the original repository:**
   - https://github.com/RUB-SysSec/DroneSecurity

2. **Click "Fork" button** (top right corner)

3. **Configure fork:**
   - Owner: Select "Skeletoskull"
   - Repository name: Keep as "DroneSecurity"
   - Description: "Windows port with BladeRF A4 support"
   - ✅ Copy the main branch only
   - Click "Create fork"

4. **Wait for fork to complete** (usually takes 10-30 seconds)

---

## Step 6: Clone Your Fork

```powershell
# Navigate to where you want to store the project
cd D:\Projects  # or your preferred location

# Clone your fork
git clone https://github.com/Skeletoskull/DroneSecurity.git

# Navigate into the cloned repository
cd DroneSecurity

# Verify it worked
git status
# Should show: "On branch main"
```

---

## Step 7: Add Upstream Remote

```powershell
# Add the original repository as "upstream"
git remote add upstream https://github.com/RUB-SysSec/DroneSecurity.git

# Verify remotes
git remote -v
# Should show:
# origin    https://github.com/Skeletoskull/DroneSecurity.git (fetch)
# origin    https://github.com/Skeletoskull/DroneSecurity.git (push)
# upstream  https://github.com/RUB-SysSec/DroneSecurity.git (fetch)
# upstream  https://github.com/RUB-SysSec/DroneSecurity.git (push)
```

---

## Step 8: Create Feature Branch

```powershell
# Create and switch to new branch
git checkout -b windows-bladerf-support

# Verify you're on the new branch
git branch
# Should show: * windows-bladerf-support
```

---

## Step 9: Copy Your Modified Files

Now you need to copy your modified files from your current project directory to the cloned repository.

### Manual Method (Recommended for first time)

1. Open two File Explorer windows:
   - Window 1: Your current project: `D:\Drone Classifier\BladeRF`
   - Window 2: Cloned repository: `D:\Projects\DroneSecurity`

2. Copy these files/folders from Window 1 to Window 2:
   - `src/` folder (overwrite all files)
   - `tests/` folder (overwrite all files)
   - `requirements.txt` (overwrite)
   - `SYSTEM_OVERVIEW.md` (new file)
   - `DJI_DroneID_Live_Receiver_Pipeline.md` (new file)
   - `.gitignore` (overwrite)

3. **DO NOT copy:**
   - `.venv/` folder
   - `__pycache__/` folders
   - `.pytest_cache/` folder
   - `.hypothesis/` folder
   - Sample files (they're already in the fork)
   - Compiled files (*.pyc)

### PowerShell Method (Advanced)

```powershell
# From your current project directory
$source = "D:\Drone Classifier\BladeRF"
$dest = "D:\Projects\DroneSecurity"

# Copy source files
Copy-Item "$source\src\*" "$dest\src\" -Recurse -Force

# Copy tests
Copy-Item "$source\tests\*" "$dest\tests\" -Recurse -Force

# Copy documentation
Copy-Item "$source\SYSTEM_OVERVIEW.md" "$dest\" -Force
Copy-Item "$source\DJI_DroneID_Live_Receiver_Pipeline.md" "$dest\" -Force
Copy-Item "$source\requirements.txt" "$dest\" -Force
Copy-Item "$source\.gitignore" "$dest\" -Force
```

---

## Step 10: Update README

1. Open `D:\Projects\DroneSecurity\README.md` in your text editor

2. Add the fork header from `README_FORK_HEADER.md` to the TOP of the file

3. Keep all the original content below

4. Save the file

---

## Step 11: Review Changes

```powershell
# Navigate to the cloned repository
cd D:\Projects\DroneSecurity

# Check what files changed
git status

# See detailed changes
git diff

# See changes in a specific file
git diff src/droneid_receiver_live.py
```

---

## Step 12: Stage and Commit Changes

```powershell
# Stage all changes
git add .

# Verify what will be committed
git status

# Commit with detailed message
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

---

## Step 13: Push to GitHub

```powershell
# Push your branch to GitHub
git push origin windows-bladerf-support

# If this is the first push, you might need to set upstream:
git push -u origin windows-bladerf-support
```

**Note:** Git will ask for your GitHub credentials:
- Username: `Skeletoskull`
- Password: Paste your **Personal Access Token** (not your GitHub password!)

---

## Step 14: Verify on GitHub

1. Go to: https://github.com/Skeletoskull/DroneSecurity
2. You should see a banner: "windows-bladerf-support had recent pushes"
3. Click "Compare & pull request" (if you want to create a PR to upstream)
4. Or just browse your branch to verify files are there

---

## Step 15: Set Default Branch (Optional)

If you want your Windows branch to be the default:

1. Go to: https://github.com/Skeletoskull/DroneSecurity/settings
2. Click "Branches" in left sidebar
3. Under "Default branch", click the switch icon
4. Select "windows-bladerf-support"
5. Click "Update"
6. Confirm the change

---

## Step 16: Add Repository Details

1. **Go to your repository:**
   - https://github.com/Skeletoskull/DroneSecurity

2. **Click the gear icon** (⚙️) next to "About" (top right)

3. **Fill in details:**
   - Description: `Windows port of DroneSecurity with BladeRF A4 support - DJI DroneID receiver (NDSS 2023)`
   - Website: `https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf`
   - Topics: `sdr`, `dji`, `droneid`, `bladerf`, `gnuradio`, `windows`, `ofdm`, `qpsk`, `drone-security`, `ndss`
   - ✅ Include in the home page

4. **Click "Save changes"**

---

## Troubleshooting

### "git: command not found"
- Git is not installed or not in PATH
- Restart your terminal after installing Git
- Try running: `C:\Program Files\Git\bin\git.exe --version`

### "Permission denied (publickey)"
- SSH key not set up correctly
- Use HTTPS instead: `git clone https://github.com/...`
- Or set up SSH key properly (see Step 4)

### "Authentication failed"
- Using GitHub password instead of Personal Access Token
- Generate a new token: https://github.com/settings/tokens
- Use token as password when git asks

### "fatal: not a git repository"
- You're not in the cloned repository directory
- Run: `cd D:\Projects\DroneSecurity`

### "Your branch is behind 'origin/windows-bladerf-support'"
- Someone else pushed changes (unlikely for new branch)
- Run: `git pull origin windows-bladerf-support`

### Large files warning
- Sample files might be too large for GitHub
- They're already in .gitignore, so shouldn't be an issue
- If needed, use Git LFS: https://git-lfs.github.com/

---

## Next Steps

After successfully pushing to GitHub:

1. ✅ **Share your repository** with the community
2. ✅ **Create a release** (optional): https://github.com/Skeletoskull/DroneSecurity/releases/new
3. ✅ **Add a README badge** showing it's a fork
4. ✅ **Consider creating a PR** to the original repository
5. ✅ **Star the original repository** to show appreciation

---

## Quick Reference Commands

```powershell
# Check status
git status

# See changes
git diff

# Stage all changes
git add .

# Commit changes
git commit -m "Your message"

# Push to GitHub
git push origin windows-bladerf-support

# Pull latest changes
git pull origin windows-bladerf-support

# Switch branches
git checkout main
git checkout windows-bladerf-support

# Update from upstream
git fetch upstream
git merge upstream/main
```

---

## Need Help?

- **Git Documentation:** https://git-scm.com/doc
- **GitHub Guides:** https://guides.github.com/
- **Git Cheat Sheet:** https://education.github.com/git-cheat-sheet-education.pdf
- **Stack Overflow:** https://stackoverflow.com/questions/tagged/git

---

**Good luck! You're about to share your awesome Windows port with the world!** 🚀
