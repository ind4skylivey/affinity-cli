# affinity-cli

Professional Linux helper for installing Affinity Photo, Designer, and Publisher with Wine using the installers you already own.

> **Important:** affinity-cli never downloads or redistributes Affinity installers. Place your legally obtained installers inside this repository and the CLI will take it from there.

## Contents
- [Prerequisites](#prerequisites)
- [Installer preparation](#installer-preparation)
- [Installation](#installation)
- [CLI usage](#cli-usage)
- [Configuration file](#configuration-file)
- [Examples](#examples)
- [Status information](#status-information)
- [Legal notice](#legal-notice)

## Prerequisites
- Linux distribution with Python 3.8+
- Wine or Proton already installed on the system
- Official Affinity installers purchased from Serif

## Installer preparation
1. Create the directory `./affinity-installers/` at the root of this repository.
2. Copy your installers into that folder. Supported file name patterns:
   - `affinity-photo-1.10.6.exe`
   - `affinity-photo-msi-2.6.5.exe`
   - `affinity-designer-1.10.6.exe`
   - `affinity-designer-msi-2.6.5.exe`
   - `affinity-publisher-1.10.6.exe`
   - `affinity-publisher-msi-2.6.5.exe`
3. Version 2 installers include `-msi-` in the file name. affinity-cli automatically prefers v2 installers unless you pin v1 explicitly.

You can store multiple versions of each product; the CLI will pick the newest file for each combination.

## Installation
```bash
git clone https://github.com/ind4skylivey/affinity-cli.git
cd affinity-cli
pip install -e .
```

## CLI usage
```
affinity-cli list-installers   # show everything that can be installed
affinity-cli install photo     # install Photo (use designer/publisher/all)
affinity-cli install all --dry-run  # preview commands without running
affinity-cli install designer --version v1  # force version 1 installer
affinity-cli status            # review config and available installers
```

Global options for every command:
- `--config PATH` — use an alternate configuration file.

Command options:
- `--installers-path PATH` — override the installer directory for the current command.
- `--prefix PATH` — specify a custom Wine prefix (default: `~/.wine-affinity`).
- `--version v1|v2` — force a specific installer generation for the install command.
- `--silent` — pass `/quiet` to the installer.
- `--dry-run` — print Wine commands without executing them.

## Configuration file
Optional file: `~/.config/affinity-cli/config.toml`

```toml
installers_path = "/home/user/projects/affinity-cli/affinity-installers"
wine_prefix = "/home/user/.wine-affinity"
default_version = "v2"  # use "v1" to always choose legacy installers
```

Environment variables override these values when set:
- `AFFINITY_INSTALLERS_PATH`
- `AFFINITY_WINE_PREFIX`
- `AFFINITY_DEFAULT_VERSION`

## Examples
```bash
# Install every product silently into a custom prefix
affinity-cli install all --silent --prefix ~/.wine-affinity-suite

# Install only Publisher using a specific installer directory
affinity-cli install publisher --installers-path ./downloads

# List installers found via the configuration file
affinity-cli list-installers
```

## Status information
`affinity-cli status` prints:
- Current installer directory and whether it exists
- Wine prefix location and whether it already exists
- Default version preference
- Summary of every detected installer

## Legal notice
This project is an unofficial helper and **does not distribute Affinity applications**. Users must supply their own installers and comply with Serif's license terms.
