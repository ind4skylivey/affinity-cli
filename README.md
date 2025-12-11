# Affinity CLI · v2.0.0
<img width="1536" height="1024" alt="banner" src="https://github.com/user-attachments/assets/8a87fa64-581f-4bdc-b8f0-e1721fab35e9" />

**One Command. Zero Friction.**
Install the Affinity Universal app on Linux with a prepared Wine environment.

[![Release](https://img.shields.io/github/v/release/ind4skylivey/affinity-cli?label=release&color=blueviolet)](https://github.com/ind4skylivey/affinity-cli/releases/tag/v2.0.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Wine](https://img.shields.io/badge/Wine-10.x-red?logo=wine&logoColor=white)](https://www.winehq.org/)

---

## Why Affinity CLI?

- Universal installer: downloads and runs the official Affinity Universal EXE.
- Guided Wine setup: prepares a 64‑bit Windows 11 prefix with required components.
- Profiles for speed vs. completeness: minimal, standard (default), full.
- Clear, non-interactive flow with preflight checks and progress logs.

---

## Prerequisites

- Python 3.8+
- `winetricks`, `curl`, `tar`, `python3` on the host
- Vulkan drivers if you plan to use DXVK (recommended)

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

## Developer install (from git)

```bash
git clone https://github.com/ind4skylivey/affinity-cli.git
cd affinity-cli
git checkout release/v2.0.0
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Upgrading from an older checkout? Run:

```bash
git pull
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---
<img width="1053" height="658" alt="32423451" src="https://github.com/user-attachments/assets/9aa14019-7de2-437e-8112-8f32a65e438e" />
## Wine Runtime Setup (optional but recommended)

Affinity CLI can prepare a prefix on first run. If you prefer a pinned, portable runtime, use the companion repo [`affinity-wine-setup`](https://github.com/ind4skylivey/affinity-wine-setup).

### Quick start

```bash
curl -LO https://raw.githubusercontent.com/ind4skylivey/affinity-wine-setup/main/setup-wine-ge.sh
chmod +x setup-wine-ge.sh
GE_TAG=GE-Proton10-25 ./setup-wine-ge.sh
```

This creates a clean prefix at `~/.wine-affinity`, sets Windows 10, and installs .NET 3.5 SP1, .NET 4.8, DXVK, and VKD3D using Proton-GE.

### Run Affinity CLI with the prepared runtime

```bash
WINEPREFIX=$HOME/.wine-affinity \
WINE=$HOME/.local/share/Proton-GE/GE-Proton10-25/files/bin/wine \
affinity-cli <command>
```

### Custom options

- `WINVER_TARGET`: `win10` (default) or `win11`
- `WINEPREFIX`: destination prefix (default `~/.wine-affinity`)
- `WINE_BIN` / `WINESERVER_BIN`: use your own Wine build; set `SKIP_DOWNLOAD=1` to skip Proton-GE download
- `GITHUB_TOKEN`: optional, avoids GitHub API rate limits when using `latest`

### Verify

```bash
WINEPREFIX=$HOME/.wine-affinity \
WINE=$HOME/.local/share/Proton-GE/GE-Proton10-25/files/bin/wine \
$WINE winecfg
```

If `winecfg` opens without WoW64 experimental warnings, the runtime is ready.

---
## Screenshots

### CLI workflow

<p align="center">
  <img src="https://github.com/user-attachments/assets/39614f0d-4aad-4142-b855-b0f8a42154fb"
       width="420"
       alt="Affinity CLI running install workflow in terminal" />
</p>

### Affinity running on Linux

Real installs created with Affinity-CLI on Linux desktops:

<img
  src="https://github.com/user-attachments/assets/aa766d18-0b77-42f0-a3d4-16639da6f04f"
  width="900"
  alt="Affinity Universal installer and Affinity apps running on a Linux desktop"
/>

<img
  src="https://github.com/user-attachments/assets/edf2c1af-aa0a-4042-ba88-5f7afd9e3e77"
  width="900"
  alt="Affinity Photo running on Linux using the Affinity-CLI Wine setup"
/>

<img
  src="https://github.com/user-attachments/assets/bdfa1708-66a0-43af-953e-226dad1cb7c3"
  width="900"
  alt="Affinity apps launched on Linux after installation with Affinity-CLI"
/>



## First Run: Prefix Preparation

- The first `affinity-cli install` creates a dedicated 64-bit Wine prefix set to Windows 11.
- Installs Windows components via winetricks (depending on profile).
- Initial setup can take several minutes (10–20 on the “full” profile).
- During this time you may see logs like:
  - `winetricks is still running... please wait`
  - `Preparing: C:\...\netfx_....msi...`
- Subsequent runs reuse the prepared prefix and are much faster.
- Do **not** close the terminal during this step.

---

## Wine Profiles

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
affinity-cli install                      # preflight -> prepare prefix -> download/run installer -> verify
affinity-cli install --preflight-only
affinity-cli install --dry-run
affinity-cli install --silent
affinity-cli install --prefix ~/.wine-affinity-pro
affinity-cli install --download-url https://downloads.affinity.studio/Affinity%20x64.exe
affinity-cli install --wine-profile minimal|standard|full
```

---

## Troubleshooting

- Windows version warning: rerun with a clean prefix or try the **full** profile.
- Logs: set `AFFINITY_CLI_LOG=DEBUG` and rerun.
- Download issues: use `--download-url` or set `AFFINITY_DOWNLOAD_URL`.

---

## Roadmap

- Pre-built Wine runtime & prefix: optional downloadable, pre-configured runtime/prefix to speed up first install.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Acknowledgments

- Wine, DXVK, VKD3D and all contributors.
- Everyone opening issues, testing builds, and sharing feedback.


## 🌑 Why We Do This

Native Linux support shouldn't be a luxury, yet we often find ourselves as the forgotten ones—the children of the night in the creative software world. 

It costs nothing to acknowledge the Linux community, but since the industry won't build it for us, **we build it ourselves.**

Affinity-Cli exists to bridge that gap. We implement what others ignore, proving that creativity has no OS boundaries. If they won't give us the tools, we'll forge the path to run them anyway.

*For the creators, the hackers, and the forgotten ones.*

## 🤝 Community & Support

Affinity-Cli is an open-source project built by and for the Linux creative community.

- **Found a bug?** Please [open an issue](https://github.com/ind4skylivey/affinity-cli/issues) with your logs and distribution details.
- **Have an idea?** We welcome feature requests and pull requests!
- **Wine trouble?** Wine configuration can be tricky. If you encounter specific Wine errors, check the [Troubleshooting](#troubleshooting) section or try using a clean prefix.

This project is not affiliated with Serif (Affinity). It is a community tool to help you run the software you own on the OS you love.

## 🎨 Creative Freedom Fund

Native Linux support shouldn't be a luxury. If this tool helped you ditch Windows and keep creating, consider supporting the project.

<div align="center">

[![BTC](https://img.shields.io/badge/Bitcoin-bc1q...fur5k-f7931a?style=flat-square&logo=bitcoin)](https://mempool.space/address/bc1qg4he7nyq4j5r8mzq23e8shqvtvuymtmq5fur5k)
[![ETH](https://img.shields.io/badge/Ethereum-0x21...b765-627eea?style=flat-square&logo=ethereum)](https://etherscan.io/address/0x21C8864A17324e907A7DCB8d70cD2C5030c5b765)
[![SOL](https://img.shields.io/badge/Solana-BS3N...2e4-9945FF?style=flat-square&logo=solana)](https://solscan.io/account/BS3Nze14rdkPQQ8UkQZP4SU8uSc6de3UaVmv8gqh52e4)
[![XMR](https://img.shields.io/badge/Monero-86dX...FJs-ff6600?style=flat-square&logo=monero&logoColor=white)](https://www.getmonero.org/)

<br>

<img src=".github/assets/btc-qr.png" width="160" alt="BTC QR">
<img src=".github/assets/eth-qr.png" width="160" alt="ETH QR">
<img src=".github/assets/sol-qr.png" width="160" alt="SOL QR">
<img src=".github/assets/xmr-qr.png" width="160" alt="XMR QR">

</div>
