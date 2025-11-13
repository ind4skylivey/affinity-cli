"""
Distro Detector Module
Automatically identifies Linux distribution and package manager
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict
from enum import Enum


class PackageManager(Enum):
    """Supported package managers"""
    APT = "apt"          # Debian/Ubuntu
    DNF = "dnf"          # Fedora/RHEL/CentOS
    YUM = "yum"          # Older Fedora/RHEL
    PACMAN = "pacman"    # Arch/Manjaro/Garuda
    ZYPPER = "zypper"    # openSUSE
    APTITUDE = "aptitude"  # Debian fallback


class DistroFamily(Enum):
    """Linux distro families"""
    DEBIAN = "debian"
    FEDORA = "fedora"
    ARCH = "arch"
    SUSE = "suse"
    UNKNOWN = "unknown"


class DistroDetector:
    """Detect Linux distribution and package manager"""
    
    # Distro identifier mappings
    DISTRO_MAPPING = {
        # Debian family
        "ubuntu": (DistroFamily.DEBIAN, PackageManager.APT),
        "debian": (DistroFamily.DEBIAN, PackageManager.APT),
        "linuxmint": (DistroFamily.DEBIAN, PackageManager.APT),
        "elementary": (DistroFamily.DEBIAN, PackageManager.APT),
        "pop": (DistroFamily.DEBIAN, PackageManager.APT),
        "popos": (DistroFamily.DEBIAN, PackageManager.APT),
        "deepin": (DistroFamily.DEBIAN, PackageManager.APT),
        
        # Fedora family
        "fedora": (DistroFamily.FEDORA, PackageManager.DNF),
        "rhel": (DistroFamily.FEDORA, PackageManager.DNF),
        "centos": (DistroFamily.FEDORA, PackageManager.DNF),
        "rocky": (DistroFamily.FEDORA, PackageManager.DNF),
        "almalinux": (DistroFamily.FEDORA, PackageManager.DNF),
        
        # Arch family
        "arch": (DistroFamily.ARCH, PackageManager.PACMAN),
        "manjaro": (DistroFamily.ARCH, PackageManager.PACMAN),
        "garuda": (DistroFamily.ARCH, PackageManager.PACMAN),
        "endeavouros": (DistroFamily.ARCH, PackageManager.PACMAN),
        "cachyos": (DistroFamily.ARCH, PackageManager.PACMAN),
        "artix": (DistroFamily.ARCH, PackageManager.PACMAN),
        
        # SUSE family
        "opensuse": (DistroFamily.SUSE, PackageManager.ZYPPER),
        "opensuse-leap": (DistroFamily.SUSE, PackageManager.ZYPPER),
        "opensuse-tumbleweed": (DistroFamily.SUSE, PackageManager.ZYPPER),
        "suse": (DistroFamily.SUSE, PackageManager.ZYPPER),
    }
    
    def __init__(self):
        self.distro_id = None
        self.distro_name = None
        self.distro_version = None
        self.distro_family = None
        self.package_manager = None
        self._detect()
    
    def _detect(self):
        """Auto-detect distro and package manager"""
        # Try /etc/os-release first (Linux standard)
        if self._parse_os_release():
            return
        
        # Try LSB release
        if self._parse_lsb_release():
            return
        
        # Try distro-specific files
        self._parse_distro_files()
    
    def _parse_os_release(self) -> bool:
        """Parse /etc/os-release (primary method)"""
        os_release_path = Path("/etc/os-release")
        
        if not os_release_path.exists():
            return False
        
        try:
            with open(os_release_path, 'r') as f:
                content = f.read()
            
            # Extract ID, ID_LIKE, and VERSION
            id_match = re.search(r'^ID=(["\']?)([^\'"]+)\1', content, re.MULTILINE)
            id_like_match = re.search(r'^ID_LIKE=(["\']?)([^\'"]+)\1', content, re.MULTILINE)
            version_match = re.search(r'VERSION_ID=(["\']?)([^\'"]+)\1', content, re.MULTILINE)
            name_match = re.search(r'NAME=(["\']?)([^\'"]+)\1', content, re.MULTILINE)
            
            if id_match:
                self.distro_id = id_match.group(2).lower()
                self.distro_version = version_match.group(2) if version_match else "unknown"
                self.distro_name = name_match.group(2) if name_match else self.distro_id
                
                # Check ID_LIKE for derivative distros (e.g., CachyOS = arch)
                if id_like_match and self.distro_id not in self.DISTRO_MAPPING:
                    id_like = id_like_match.group(2).lower().split()[0]  # Take first if multiple
                    if id_like in self.DISTRO_MAPPING:
                        self.distro_id = id_like
                
                # Map to family and package manager
                self._map_distro()
                return True
            
        except Exception:
            pass
        
        return False
    
    def _parse_lsb_release(self) -> bool:
        """Parse /etc/lsb-release (Ubuntu/Debian fallback)"""
        try:
            result = subprocess.run(
                ["lsb_release", "-i", "-r"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                distro_line = result.stdout.split('\n')[0]
                match = re.search(r':\s*(.+)', distro_line)
                if match:
                    self.distro_id = match.group(1).lower().strip()
                    self.distro_name = match.group(1).strip()
                    self._map_distro()
                    return True
        except Exception:
            pass
        
        return False
    
    def _parse_distro_files(self):
        """Fallback: check distro-specific release files"""
        distro_files = {
            "/etc/fedora-release": "fedora",
            "/etc/arch-release": "arch",
            "/etc/redhat-release": "rhel",
            "/etc/os-release": "linux",
        }
        
        for file_path, distro in distro_files.items():
            if Path(file_path).exists():
                self.distro_id = distro
                self.distro_name = distro.capitalize()
                self._map_distro()
                break
    
    def _map_distro(self):
        """Map distro ID to family and package manager"""
        if self.distro_id in self.DISTRO_MAPPING:
            family, pm = self.DISTRO_MAPPING[self.distro_id]
            self.distro_family = family
            self.package_manager = pm
        else:
            # Unknown distro, try to guess
            self.distro_family = DistroFamily.UNKNOWN
            self._guess_package_manager()
    
    def _guess_package_manager(self):
        """Try to guess package manager by checking available commands"""
        pms_to_check = [
            PackageManager.APT,
            PackageManager.DNF,
            PackageManager.PACMAN,
            PackageManager.ZYPPER,
        ]
        
        for pm in pms_to_check:
            if self._command_exists(pm.value):
                self.package_manager = pm
                break
        
        if not self.package_manager:
            self.package_manager = PackageManager.APT  # Default fallback
    
    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if a command is available in PATH"""
        try:
            subprocess.run(
                ["which", command],
                capture_output=True,
                timeout=2
            )
            return True
        except Exception:
            return False
    
    def get_distro_info(self) -> Dict[str, str]:
        """Return distro information as dictionary"""
        return {
            "id": self.distro_id,
            "name": self.distro_name,
            "version": self.distro_version,
            "family": self.distro_family.value if self.distro_family else "unknown",
            "package_manager": self.package_manager.value if self.package_manager else "unknown",
        }
    
    def get_package_manager_info(self) -> Dict[str, str]:
        """Get package manager commands for this distro"""
        pm_commands = {
            PackageManager.APT: {
                "install": "sudo apt-get install -y",
                "search": "apt-cache search",
                "update": "sudo apt-get update",
                "multiarch": "sudo dpkg --add-architecture i386 && sudo apt-get update",
            },
            PackageManager.DNF: {
                "install": "sudo dnf install -y",
                "search": "dnf search",
                "update": "sudo dnf check-update",
                "multiarch": "sudo dnf install -y glibc.i686 libstdc++.i686",
            },
            PackageManager.PACMAN: {
                "install": "sudo pacman -S --noconfirm",
                "search": "pacman -Ss",
                "update": "sudo pacman -Syy",
                "multiarch": "Edit /etc/pacman.conf to enable multilib",
            },
            PackageManager.ZYPPER: {
                "install": "sudo zypper install -y",
                "search": "zypper search",
                "update": "sudo zypper refresh",
                "multiarch": "sudo zypper install -y glibc-32bit",
            },
        }
        
        if self.package_manager in pm_commands:
            return pm_commands[self.package_manager]
        
        return {}
    
    @staticmethod
    def is_root() -> bool:
        """Check if running as root"""
        return os.getuid() == 0


# Simple interface for external use
def detect_distro() -> Tuple[str, str, PackageManager]:
    """
    Detect current Linux distribution and package manager
    
    Returns:
        (distro_name, distro_version, package_manager)
    """
    detector = DistroDetector()
    info = detector.get_distro_info()
    return (info["name"], info["version"], detector.package_manager)


def detect_package_manager() -> Tuple[PackageManager, str, bool]:
    """
    Detect package manager and return common commands
    
    Returns:
        (package_manager, install_command, sudo_required)
    """
    detector = DistroDetector()
    pm_info = detector.get_package_manager_info()
    
    return (
        detector.package_manager,
        pm_info.get("install", ""),
        not DistroDetector.is_root()
    )


# For testing
if __name__ == "__main__":
    detector = DistroDetector()
    print("=== Distro Detection ===")
    print(f"Distro: {detector.distro_name}")
    print(f"Version: {detector.distro_version}")
    print(f"Family: {detector.distro_family.value if detector.distro_family else 'unknown'}")
    print(f"Package Manager: {detector.package_manager.value if detector.package_manager else 'unknown'}")
    print("\n=== Package Manager Commands ===")
    for cmd, value in detector.get_package_manager_info().items():
        print(f"{cmd}: {value}")
