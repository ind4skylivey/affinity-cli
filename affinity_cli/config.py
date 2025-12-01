"""Global configuration and internal defaults for Affinity CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

# Project metadata ---------------------------------------------------------

VERSION = "2.0.0"
APP_NAME = "Affinity CLI"

# Paths --------------------------------------------------------------------

HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".config" / "affinity-cli"
CACHE_DIR = HOME_DIR / ".cache" / "affinity-cli"
DEFAULT_INSTALLERS_PATH = HOME_DIR / "Downloads" / "affinity-installers"
DEFAULT_WINE_PREFIX = HOME_DIR / ".wine-affinity"
DEFAULT_WINE_INSTALL = HOME_DIR / ".local" / "wine"
DEFAULT_UNIVERSAL_URL = "https://downloads.affinity.studio/Affinity%20x64.exe"

# Versions -----------------------------------------------------------------

DEFAULT_INSTALLER_VERSION = "universal"
SUPPORTED_INSTALLER_VERSIONS = ("universal",)

# Wine ---------------------------------------------------------------------

WINE_VERSION_DEFAULT = "latest"
ELEMENTALWARRIOR_REPO = "https://gitlab.com/elementalwarrior/wine"

# Installer discovery -------------------------------------------------------

UNIVERSAL_INSTALLER_FILENAME = "Affinity_Universal.exe"
INSTALLER_SUFFIXES = (".exe", ".msi", ".msix")
INSTALLER_NAME_PREFIX = "affinity"

# Affinity Products --------------------------------------------------------

AFFINITY_PRODUCTS: Dict[str, Dict[str, str]] = {
    "photo": {
        "name": "Affinity Photo",
        "exe_name": "Photo.exe",
        "install_path": "Program Files/Affinity/Photo 2",
    },
    "designer": {
        "name": "Affinity Designer",
        "exe_name": "Designer.exe",
        "install_path": "Program Files/Affinity/Designer 2",
    },
    "publisher": {
        "name": "Affinity Publisher",
        "exe_name": "Publisher.exe",
        "install_path": "Program Files/Affinity/Publisher 2",
    },
}

# Dependencies by category -------------------------------------------------

CORE_WINE_DEPS = [
    "wine",
    "wine64",
    "libwine",
]

MULTIARCH_32BIT_DEPS = [
    "libc6:i386",
    "libgcc-s1:i386",
    "libstdc++6:i386",
    "libx11-6:i386",
    "libxext6:i386",
]

GRAPHICS_DEPS = [
    "libvulkan1",
    "libvulkan1:i386",
    "libgl1-mesa-glx",
    "libgl1-mesa-glx:i386",
    "libxrender1",
    "libxrender1:i386",
]

FONT_DEPS = [
    "fontconfig",
    "fontconfig:i386",
    "fonts-dejavu",
    "fonts-liberation",
]

BUILD_DEPS = [
    "build-essential",
    "gcc",
    "gcc-multilib",
    "bison",
    "flex",
]

# Ensure config directories exist (best-effort; ignore permission errors) --
for path in (CONFIG_DIR, CACHE_DIR):
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # In restricted environments we still want imports to succeed.
        pass

# Convenience re-exports ----------------------------------------------------
# Imported lazily to avoid circular imports during module initialization.
from affinity_cli.core.config_loader import ConfigLoader, ConfigError, ResolvedConfig, UserConfig  # noqa: E402,F401

__all__ = [
    "ConfigLoader",
    "ConfigError",
    "ResolvedConfig",
    "UserConfig",
    "VERSION",
    "APP_NAME",
    "HOME_DIR",
    "CONFIG_DIR",
    "CACHE_DIR",
    "DEFAULT_INSTALLERS_PATH",
    "DEFAULT_WINE_PREFIX",
    "DEFAULT_WINE_INSTALL",
    "DEFAULT_INSTALLER_VERSION",
    "SUPPORTED_INSTALLER_VERSIONS",
    "UNIVERSAL_INSTALLER_FILENAME",
    "WINE_VERSION_DEFAULT",
    "ELEMENTALWARRIOR_REPO",
    "INSTALLER_SUFFIXES",
    "INSTALLER_NAME_PREFIX",
    "AFFINITY_PRODUCTS",
    "CORE_WINE_DEPS",
    "MULTIARCH_32BIT_DEPS",
    "GRAPHICS_DEPS",
    "FONT_DEPS",
    "BUILD_DEPS",
]
