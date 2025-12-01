<div align="center">

![Affinity CLI Hero](.github/assets/affinity-cli-hero.png)

# 🎨 Affinity CLI · v2.0.0

### One Command. Zero Friction.

[![GitHub stars](https://img.shields.io/github/stars/ind4skylivey/affinity-cli?style=for-the-badge)](https://github.com/ind4skylivey/affinity-cli)
[![CI](https://img.shields.io/github/actions/workflow/status/ind4skylivey/affinity-cli/tests.yml?style=for-the-badge&label=CI)](https://github.com/ind4skylivey/affinity-cli/actions)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**Affinity CLI** is the universal Linux installer for the new Affinity Universal app bundle. It automates preflight checks, downloads the official universal installer with smart resume/proxy support, and sets up Wine so all Affinity apps land in one smooth run.

**[Quick Start](#-quick-start) • [Features](#-features) • [Commands](#-commands) • [Troubleshooting](#-troubleshooting)**

</div>

---

## 🌟 What is Affinity CLI?

The fastest way to install the Affinity Universal bundle on Linux. One command handles:

- **Preflight**: disk space, cache perms, Wine/Proton presence, Vulkan/GPU hints, distro detection.
- **Smart download**: proxy-aware, resumable, retrying downloader that fetches the official universal installer.
- **Install & verify**: runs the installer once under Wine and confirms app binaries landed.

> **No more manual Wine tuning. No more hunting three separate installers. One Command. Zero Friction.** 🚀

---

## ⚡ Quick Start

```bash
# From source
git clone https://github.com/ind4skylivey/affinity-cli.git
cd affinity-cli
python3 -m venv .venv
source .venv/bin/activate  # or .venv/bin/activate.fish
python -m pip install --upgrade pip
python -m pip install -e .

# Pre-flight only (safe, no changes)
affinity-cli install --preflight-only

# Install (downloads if needed, then installs)
affinity-cli install
```

---

## 🎯 Features

- **Universal-first**: single Affinity Universal EXE installs Photo, Designer, and Publisher in one pass.
- **Smart Downloader**: retries, resume, proxy awareness, SHA256 verification, non-interactive env vars.
- **Preflight Guardrails**: disk, cache perms (700), Wine/Proton detection, Vulkan hinting, distro/package-manager awareness.
- **Automation Friendly**: `--preflight-only`, `--dry-run`, `--silent`, `--prefix` overrides.
- **Minimal Cognitive Load**: defaults that “just work”; prompts only when absolutely necessary.

---

---

## 🚀 Quick Start

### ⚡ Installation (3 simple steps)

## 🛠 Commands

```bash
affinity-cli install             # Full flow: preflight -> download -> install -> verify
affinity-cli install --preflight-only
affinity-cli install --dry-run
affinity-cli install --silent
affinity-cli install --prefix ~/.wine-affinity-pro
affinity-cli install --download-url https://downloads.affinity.studio/Affinity%20x64.exe
affinity-cli install --wine-profile minimal|standard|full
```

> Positional product targets (photo/designer/publisher) are no longer supported. Use the universal install flow above.

### First run: Wine prefix preparation

- On the first `affinity-cli install`, a dedicated 64-bit Wine prefix is prepared.
- The prefix is set to Windows 11 and installs Windows components via winetricks (corefonts, runtimes, DXVK/VKD3D, etc. depending on profile).
- The initial setup can take several minutes—especially with the **full** profile.
- During this time you may see logs like:
  - `winetricks is still running... please wait`
  - `Preparing: C:\...\netfx_....msi...`
- Subsequent runs reuse the prepared prefix and are much faster.

**Do not panic:**
- It is normal for the first install to take several minutes.
- Do not close the terminal while winetricks is running.
- If something fails, run `affinity-cli install --preflight-only` and then `affinity-cli install` again.

> During prefix preparation you will see winetricks output and messages like “winetricks is still running… please wait.” This is expected on first run—do not close the terminal. Depending on hardware and profile (especially “full”), this can take 10–20 minutes.

### Wine profiles

- **minimal** – fastest, smallest set (for advanced users): win11, corefonts, tahoma, crypt32, d3dcompiler_47
- **standard** (default) – recommended balance: minimal + vcrun2022
- **full** – maximum compatibility; first run can take 10–20 minutes: standard + dotnet48, dxvk, vkd3d, remove_mono

Examples:
```bash
affinity-cli install --wine-profile minimal
affinity-cli install --wine-profile standard   # default
affinity-cli install --wine-profile full

# via environment variable
AFFINITY_WINE_PROFILE=full affinity-cli install
```

## ✅ Verification & Launch

- Check binaries: `find ~/.wine-affinity -name "Photo.exe" -o -name "Designer.exe" -o -name "Publisher.exe"`
- Launch (example): `wine64 ~/.wine-affinity/drive_c/Program\ Files/Affinity/Photo\ 2/Photo.exe &`
- Status: `affinity-cli status` (shows distro, installers, Wine prefix, installed apps)

---

## 🤝 Contributing & Support

- Issues and PRs welcome at GitHub.
- Keep changes focused on the universal installer flow.
- For logs, include `AFFINITY_CLI_LOG=DEBUG` and the output of `affinity-cli status`.

## 🧭 Roadmap

- Pre-built Wine runtime & prefix: optional downloadable, pre-configured runtime/prefix to make the first install even faster and more consistent.

---

## 🙏 Thank You

Thanks to the Linux and Affinity community for testing, filing bugs, and sharing configs. Your feedback made the v2.0.0 release possible. Onward!

---

## 🐧 Supported Distributions (tested)

<div align="center">

<table>
<tr>
<td align="center" width="25%">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/ubuntu/ubuntu-original.svg" width="64" height="64" alt="Ubuntu"/>
<br><b>Ubuntu</b>
<br>20.04 • 22.04 • 24.04
</td>
<td align="center" width="25%">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/debian/debian-original.svg" width="64" height="64" alt="Debian"/>
<br><b>Debian</b>
<br>11 • 12 (Bookworm)
</td>
<td align="center" width="25%">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fedora/fedora-original.svg" width="64" height="64" alt="Fedora"/>
<br><b>Fedora</b>
<br>38 • 39 • 40+
Tested on recent Ubuntu, Debian, Fedora, Arch/Manjaro, and openSUSE releases. Other systemd-based distros typically work—open an issue with logs if something breaks.

---

<details>
<summary>⚙️ <b>Command Reference</b></summary>

### Installation Commands

```bash
# Interactive installation
affinity-cli install

# Pre-flight only (no changes)
affinity-cli install --preflight-only

# Custom Wine prefix
affinity-cli install --prefix ~/.my-affinity

# Dry-run (log commands without executing)
affinity-cli install --dry-run
```

### Management Commands

```bash
# Check system status
affinity-cli status
affinity-cli status --verbose

# Repair broken installation
affinity-cli repair
affinity-cli repair --product photo

# Uninstall products
affinity-cli uninstall
affinity-cli uninstall --purge  # Complete removal

# Generate system report
affinity-cli report
affinity-cli report --output report.json
```

### Information Commands

```bash
# Show version
affinity-cli --version

# Show help
affinity-cli --help
affinity-cli install --help

# Welcome message
affinity-cli welcome
```

</details>

<details>
<summary>🔧 <b>Advanced Configuration</b></summary>

### Custom Configuration File

Location: `~/.config/affinity-cli/config.yml`

```yaml
wine:
  version: "latest"
  prefix_path: "~/.wine-affinity"
  graphics_api: "vulkan"

affinity:
  products:
    - photo
    - designer
  auto_detect_installers: true

system:
  enable_multiarch: true
  install_dependencies: true
```

</details>

<details>
<summary>🐛 <b>Troubleshooting</b></summary>

### Common Issues

**Issue: Installation fails on dependency step**
```bash
# Update package lists first
sudo apt update      # Ubuntu/Debian
sudo dnf update      # Fedora
sudo pacman -Sy      # Arch
```

**Issue: Products don't appear in menu**
```bash
# Rebuild desktop database
affinity-cli repair
```

**Issue: Wine prefix creation hangs**
```bash
# Kill wine processes and retry
pkill wine
affinity-cli repair
```

**Performance issues?**
- Check GPU drivers: `vulkaninfo`
- Monitor resources: `htop`
- See logs: `~/.config/affinity-cli/logs/`

</details>

---

## 🛠️ How It Works

<div align="center">

```mermaid
graph LR
    A[🚀 Start] --> B[🐧 Detect Distro]
    B --> C[📦 Install Dependencies]
    C --> D[🍷 Setup Wine]
    D --> E[⚙️ Create Prefix]
    E --> F[🎨 Install Affinity]
    F --> G[🖥️ Desktop Integration]
    G --> H[✅ Done!]
```
</div>

### 🔄 Installation Pipeline

1. **🐧 Detection Phase** - Identifies your Linux distro and package manager
2. **📦 Preparation Phase** - Installs system dependencies (wine, libraries, fonts)
3. **🍷 Wine Setup Phase** - Downloads and configures optimized Wine build
4. **⚙️ Configuration Phase** - Creates isolated Wine prefix with .NET Framework
5. **🎨 Installation Phase** - Silently installs Affinity products
6. **🖥️ Integration Phase** - Creates menu entries and bash aliases
7. **✅ Verification Phase** - Tests installation and generates report

---

## 🎯 Requirements

<table>
<tr>
<td width="50%">

### 💻 System Requirements

- **OS:** Linux (any major distro)
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Disk:** ~5GB free space
- **Network:** Internet connection

</td>
<td width="50%">

### 📥 What You Need

- **Affinity Installers** (.exe files)
  - Purchase from [affinity.serif.com](https://affinity.serif.com/)
- **Valid License** from Serif
- **sudo access** (for dependencies)

</td>
</tr>
</table>

---

## 🏗️ Project Architecture

<details>
<summary>📂 <b>Click to view project structure</b></summary>

```
affinity-cli/
├── 📦 affinity_cli/          # Main package
│   ├── 🧠 core/               # Core functionality
│   │   ├── distro_detector.py     # OS detection
│   │   ├── dependency_manager.py  # Package management
│   │   ├── wine_manager.py        # Wine setup
│   │   ├── prefix_manager.py      # Wine prefix config
│   │   ├── affinity_installer.py  # Product installation
│   │   └── desktop_integration.py # Desktop entries
│   │
│   ├── 🎮 commands/           # CLI commands
│   │   ├── install.py         # Install command
│   │   ├── status.py          # Status command
│   │   ├── uninstall.py       # Uninstall command
│   │   ├── repair.py          # Repair command
│   │   └── report.py          # Report command
│   │
│   └── 🛠️ utils/              # Utilities
│       └── logger.py          # Logging
│
├── 🧪 tests/                  # Unit tests (27 passing)
├── 🤖 .github/workflows/      # CI/CD automation
├── 📖 README.md               # This file
├── 📜 LICENSE                 # MIT License
└── 🤝 CONTRIBUTING.md         # Contribution guide
```

**Code Statistics:**
- 📊 **~2,800 lines** of Python code
- ✅ **27 unit tests** (all passing)
- 📦 **6 core modules**
- 🎮 **5 CLI commands**
- 📚 **4 documentation files**

</details>

---

## 🤝 Contributing

We ❤️ contributions! This project thrives on community support.

<div align="center">

### 🌟 **How You Can Help**

</div>

<table>
<tr>
<td align="center" width="33%">

### 🐛 Report Bugs
Found an issue?  
[Open an issue](https://github.com/ind4skylivey/affinity-cli/issues)
</td>
<td align="center" width="33%">

### 💻 Write Code
Submit pull requests  
See [CONTRIBUTING.md](CONTRIBUTING.md)
</td>
<td align="center" width="33%">

### 🧪 Test & Feedback
Try on different distros  
Share your experience
</td>
</tr>
<tr>
<td align="center" width="33%">

### 📖 Improve Docs
Help others learn  
Update documentation
</td>
<td align="center" width="33%">

### ⭐ Star the Repo
Show your support  
Help us grow!
</td>
<td align="center" width="33%">

### 📣 Spread the Word
Tell other Linux users  
Share on social media
</td>
</tr>
</table>

### 🚀 Quick Contribution Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/affinity-cli.git
cd affinity-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Make changes and submit PR! 🎉
```

---

## 📊 Project Stats

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/ind4skylivey/affinity-cli?style=social)
![GitHub forks](https://img.shields.io/github/forks/ind4skylivey/affinity-cli?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/ind4skylivey/affinity-cli?style=social)

![GitHub issues](https://img.shields.io/github/issues/ind4skylivey/affinity-cli?style=flat-square)
![GitHub pull requests](https://img.shields.io/github/issues-pr/ind4skylivey/affinity-cli?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/ind4skylivey/affinity-cli?style=flat-square)

</div>

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**Important:** This project is not affiliated with Serif Labs (makers of Affinity). It's a community-driven effort to enable Affinity products on Linux.

---

## 🙏 Acknowledgments

<div align="center">

**Special Thanks To:**

🍷 **Wine Project** - For making Windows apps run on Linux  
🎨 **Serif Labs** - For creating amazing Affinity products  
🐧 **Linux Community** - For continuous support and testing  
⚡ **ElementalWarrior** - For Affinity-optimized Wine builds  

</div>

---

## 💬 Community & Support

<div align="center">

### 🔗 **Connect With Us**

[![GitHub Issues](https://img.shields.io/badge/GitHub-Issues-red?style=for-the-badge&logo=github)](https://github.com/ind4skylivey/affinity-cli/issues)
[![GitHub Discussions](https://img.shields.io/badge/GitHub-Discussions-green?style=for-the-badge&logo=github)](https://github.com/ind4skylivey/affinity-cli/discussions)
[![Twitter](https://img.shields.io/badge/Twitter-Follow-1DA1F2?style=for-the-badge&logo=twitter)](https://twitter.com/ind4skylivey)

</div>

### 📬 Get Help

- 💬 **GitHub Discussions** - Ask questions, share ideas
- 🐛 **GitHub Issues** - Report bugs, request features
- 📧 **Email** - For private inquiries
- 🌐 **Reddit** - r/linux, r/linuxgaming, r/AffinityPhoto

---

## 🎨 Vision & Mission

<div align="center">

> ### *"Linux users deserve professional creative tools. This project proves it's possible."*

</div>

### 🎯 Our Goals

1. 🚀 **Make Affinity installation effortless** for Linux users
2. 📊 **Demonstrate demand** for official Linux support from Serif
3. 🤝 **Build a community** around professional Linux creative tools
4. 🌟 **Inspire** official Affinity Linux support

---

## 🗺️ Roadmap

<details>
<summary>🔮 <b>Future Plans</b></summary>

### ✅ Completed (v1.0.0-beta)
- [x] Core installation system
- [x] Multi-distro support
- [x] Desktop integration
- [x] CLI interface
- [x] Unit tests & CI/CD

### 🚧 In Progress (v1.1.0)
- [ ] PyPI publication
- [ ] Extended distro testing
- [ ] Performance optimizations
- [ ] Enhanced error messages

### 🔮 Planned (v2.0.0)
- [ ] GUI installer option
- [ ] Flatpak/Snap packages
- [ ] AUR package (Arch)
- [ ] GPU-specific optimizations
- [ ] Proton support (experimental)
- [ ] Multi-language support

### 🌟 Dream Features
- [ ] Official Serif collaboration
- [ ] Native Linux Affinity (one day!)

</details>

---

## 🌈 Show Your Support

<div align="center">

### ⭐ **Star this repo** if Affinity CLI helped you!

### 🔄 **Share** with other Linux creative professionals

### 💬 **Tell Serif** that Linux users exist and we want official support!

<br>

**Together, we can make Linux a first-class platform for creative professionals.** 🐧🎨

<br>

[![Star History Chart](https://api.star-history.com/svg?repos=ind4skylivey/affinity-cli&type=Date)](https://star-history.com/#ind4skylivey/affinity-cli&Date)

---

<br>

### 🚀 **Ready to revolutionize Linux creative workflows?**

**[Get Started Now ⬆️](#-quick-start)** | **[View Releases 📦](https://github.com/ind4skylivey/affinity-cli/releases)** | **[Report Issues 🐛](https://github.com/ind4skylivey/affinity-cli/issues)**

<br>

Made with ❤️ by **[ind4skylivey](https://github.com/ind4skylivey)** and the **Linux community**

**Make Serif notice. Make Windows jealous. Make Linux creators powerful.** 🔥

</div>
