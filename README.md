# Affinity CLI · v2.0.0  
**<img width="1536" height="1024" alt="banner" src="https://github.com/user-attachments/assets/93c440de-bb9d-4e05-90d6-df211eae2ade" />
One Command. Zero Friction.**  
Install the Affinity Universal app on Linux with a prepared Wine environment.

[![GitHub stars](https://img.shields.io/github/stars/ind4skylivey/affinity-cli?style=flat&color=blue)](https://github.com/ind4skylivey/affinity-cli)
[![CI](https://img.shields.io/github/actions/workflow/status/ind4skylivey/affinity-cli/tests.yml?label=CI)](https://github.com/ind4skylivey/affinity-cli/actions)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Why Affinity CLI?
- Universal installer: downloads and runs the official Affinity Universal EXE.
- Guided Wine setup: prepares a 64‑bit Windows 11 prefix with required components.
- Profiles for speed vs. completeness: minimal, standard (default), full.
- Clear, non-interactive flow with preflight checks and progress logs.

---

## Quick Start
```bash
# Clone
git clone https://github.com/ind4skylivey/affinity-cli.git
cd affinity-cli

# Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install CLI
python -m pip install --upgrade pip
python -m pip install -e .

# Install Affinity (default profile: standard)
affinity-cli install
```

---

## First run: Wine prefix preparation
- The first `affinity-cli install` creates a dedicated 64-bit Wine prefix set to Windows 11.
- Installs Windows components via winetricks (depending on profile).
- The initial setup can take several minutes (10–20 on “full” profile).
- During this time you may see logs like:
  - `winetricks is still running... please wait`
  - `Preparing: C:\...\netfx_....msi...`
- Subsequent runs reuse the prepared prefix and are much faster.
- Do **not** close the terminal during this step.

---

## Wine profiles
Choose how many components to install in the prefix:

- **minimal** – fastest, smallest set (advanced users): `win11, corefonts, tahoma, crypt32, d3dcompiler_47`
- **standard** (default) – recommended balance: minimal + `vcrun2022`
- **full** – maximum compatibility; first run can take 10–20 minutes: standard + `dotnet48, dxvk, vkd3d, remove_mono`

Examples:
```bash
affinity-cli install --wine-profile minimal
affinity-cli install --wine-profile standard   # default
affinity-cli install --wine-profile full

# via environment variable
AFFINITY_WINE_PROFILE=full affinity-cli install
```

---

## Commands
```bash
affinity-cli install             # preflight -> prepare prefix -> download/run installer -> verify
affinity-cli install --preflight-only
affinity-cli install --dry-run
affinity-cli install --silent
affinity-cli install --prefix ~/.wine-affinity-pro
affinity-cli install --download-url https://downloads.affinity.studio/Affinity%20x64.exe
affinity-cli install --wine-profile minimal|standard|full
```

---

## Troubleshooting
- Windows version warning: If the installer complains, rerun with a clean prefix or try the **full** profile.
- Logs: set `AFFINITY_CLI_LOG=DEBUG` and re-run.
- Download issues: use `--download-url` or set `AFFINITY_DOWNLOAD_URL`.

---

## Roadmap
- Pre-built Wine runtime & prefix: optional downloadable, pre-configured runtime/prefix to make the first install even faster and more consistent.

---

## License
MIT License. See [LICENSE](LICENSE).

---

## Acknowledgments
- AffinityOnLinux community for guidance on Wine/DXVK/WinRT setup.
- Wine, DXVK, VKD3D projects and contributors.
