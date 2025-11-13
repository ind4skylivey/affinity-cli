"""
Dependency Manager Module
Install all system-level dependencies required for Wine and Affinity
"""

import subprocess
import shutil
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from affinity_cli.core.distro_detector import DistroDetector, DistroFamily, PackageManager
from affinity_cli import config


class DependencyManager:
    """Manage system dependencies for Wine and Affinity installation"""
    
    def __init__(self, detector: Optional[DistroDetector] = None):
        """
        Initialize dependency manager
        
        Args:
            detector: Pre-initialized DistroDetector instance (optional)
        """
        self.detector = detector or DistroDetector()
        self.distro_family = self.detector.distro_family
        self.package_manager = self.detector.package_manager
        self.pm_info = self.detector.get_package_manager_info()
    
    def check_dependencies(self) -> Dict[str, bool]:
        """
        Check which dependencies are installed
        
        Returns:
            Dictionary mapping dependency names to installation status
        """
        dependencies = self._get_all_dependencies()
        status = {}
        
        for dep in dependencies:
            status[dep] = self._is_package_installed(dep)
        
        return status
    
    def get_missing_dependencies(self) -> List[str]:
        """
        Get list of missing dependencies
        
        Returns:
            List of package names that need to be installed
        """
        status = self.check_dependencies()
        return [dep for dep, installed in status.items() if not installed]
    
    def install_dependencies(self, skip_multiarch: bool = False) -> Tuple[bool, str]:
        """
        Install all required dependencies
        
        Args:
            skip_multiarch: Skip multiarch configuration (default: False)
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Enable multiarch first (for 32-bit support)
            if not skip_multiarch:
                success, msg = self.enable_multiarch()
                if not success:
                    return False, f"Multiarch setup failed: {msg}"
            
            # Get missing dependencies
            missing = self.get_missing_dependencies()
            
            if not missing:
                return True, "All dependencies already installed"
            
            # Install packages
            success, msg = self._install_packages(missing)
            if not success:
                return False, f"Package installation failed: {msg}"
            
            # Verify installation
            if not self.verify_dependencies():
                return False, "Dependency verification failed after installation"
            
            return True, f"Successfully installed {len(missing)} packages"
        
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def enable_multiarch(self) -> Tuple[bool, str]:
        """
        Enable 32-bit multiarch support
        
        Returns:
            Tuple of (success, message)
        """
        if self.distro_family == DistroFamily.DEBIAN:
            return self._enable_multiarch_debian()
        elif self.distro_family == DistroFamily.FEDORA:
            return self._enable_multiarch_fedora()
        elif self.distro_family == DistroFamily.ARCH:
            return self._enable_multiarch_arch()
        elif self.distro_family == DistroFamily.SUSE:
            return self._enable_multiarch_suse()
        else:
            return True, "Multiarch not required for this distro"
    
    def verify_dependencies(self) -> bool:
        """
        Verify all critical dependencies are installed
        
        Returns:
            True if all critical dependencies present
        """
        critical_deps = self._get_critical_dependencies()
        
        for dep in critical_deps:
            if not self._is_package_installed(dep):
                return False
        
        return True
    
    def _get_all_dependencies(self) -> List[str]:
        """Get complete list of dependencies for current distro"""
        if self.distro_family == DistroFamily.DEBIAN:
            return self._get_debian_dependencies()
        elif self.distro_family == DistroFamily.FEDORA:
            return self._get_fedora_dependencies()
        elif self.distro_family == DistroFamily.ARCH:
            return self._get_arch_dependencies()
        elif self.distro_family == DistroFamily.SUSE:
            return self._get_suse_dependencies()
        else:
            return self._get_generic_dependencies()
    
    def _get_critical_dependencies(self) -> List[str]:
        """Get list of absolutely critical dependencies"""
        if self.distro_family == DistroFamily.DEBIAN:
            return ["wine", "winetricks", "fontconfig"]
        elif self.distro_family == DistroFamily.FEDORA:
            return ["wine", "winetricks", "fontconfig"]
        elif self.distro_family == DistroFamily.ARCH:
            return ["wine", "winetricks", "fontconfig"]
        else:
            return ["wine", "fontconfig"]
    
    def _get_debian_dependencies(self) -> List[str]:
        """Dependencies for Debian/Ubuntu family"""
        return [
            # Core Wine
            "wine",
            "wine64",
            "winetricks",
            
            # 32-bit multiarch
            "libc6:i386",
            "libgcc-s1:i386",
            "libstdc++6:i386",
            "libx11-6:i386",
            "libxext6:i386",
            
            # Graphics
            "libvulkan1",
            "libvulkan1:i386",
            "libgl1-mesa-glx",
            "libgl1-mesa-glx:i386",
            "libxrender1",
            "libxrender1:i386",
            
            # Fonts
            "fontconfig",
            "fontconfig:i386",
            "fonts-dejavu",
            "fonts-liberation",
            
            # Utilities
            "curl",
            "wget",
        ]
    
    def _get_fedora_dependencies(self) -> List[str]:
        """Dependencies for Fedora/RHEL family"""
        return [
            "wine",
            "winetricks",
            "glibc.i686",
            "libstdc++.i686",
            "libX11.i686",
            "vulkan-loader",
            "mesa-libGL",
            "fontconfig",
            "dejavu-fonts",
            "liberation-fonts",
            "curl",
            "wget",
        ]
    
    def _get_arch_dependencies(self) -> List[str]:
        """Dependencies for Arch family"""
        return [
            "wine",
            "winetricks",
            "lib32-glibc",
            "lib32-gcc-libs",
            "lib32-libx11",
            "vulkan-icd-loader",
            "lib32-vulkan-icd-loader",
            "mesa",
            "lib32-mesa",
            "fontconfig",
            "ttf-dejavu",
            "ttf-liberation",
            "curl",
            "wget",
        ]
    
    def _get_suse_dependencies(self) -> List[str]:
        """Dependencies for openSUSE family"""
        return [
            "wine",
            "winetricks",
            "glibc-32bit",
            "libstdc++6-32bit",
            "libX11-6-32bit",
            "Mesa",
            "fontconfig",
            "dejavu-fonts",
            "liberation-fonts",
            "curl",
            "wget",
        ]
    
    def _get_generic_dependencies(self) -> List[str]:
        """Generic fallback dependencies"""
        return [
            "wine",
            "winetricks",
            "fontconfig",
            "curl",
            "wget",
        ]
    
    def _is_package_installed(self, package: str) -> bool:
        """
        Check if a package is installed
        
        Args:
            package: Package name to check
        
        Returns:
            True if package is installed
        """
        if self.package_manager == PackageManager.APT:
            return self._is_installed_apt(package)
        elif self.package_manager == PackageManager.DNF:
            return self._is_installed_dnf(package)
        elif self.package_manager == PackageManager.PACMAN:
            return self._is_installed_pacman(package)
        elif self.package_manager == PackageManager.ZYPPER:
            return self._is_installed_zypper(package)
        else:
            return False
    
    def _is_installed_apt(self, package: str) -> bool:
        """Check if package installed via apt"""
        try:
            result = subprocess.run(
                ["dpkg", "-s", package],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _is_installed_dnf(self, package: str) -> bool:
        """Check if package installed via dnf/rpm"""
        try:
            result = subprocess.run(
                ["rpm", "-q", package],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _is_installed_pacman(self, package: str) -> bool:
        """Check if package installed via pacman"""
        try:
            result = subprocess.run(
                ["pacman", "-Q", package],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _is_installed_zypper(self, package: str) -> bool:
        """Check if package installed via zypper"""
        try:
            result = subprocess.run(
                ["rpm", "-q", package],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _install_packages(self, packages: List[str]) -> Tuple[bool, str]:
        """
        Install packages using distro package manager
        
        Args:
            packages: List of package names
        
        Returns:
            Tuple of (success, message)
        """
        if not packages:
            return True, "No packages to install"
        
        install_cmd = self.pm_info.get("install", "")
        if not install_cmd:
            return False, "Package manager install command not found"
        
        # Build full command
        cmd_parts = install_cmd.split()
        cmd_parts.extend(packages)
        
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for large installs
            )
            
            if result.returncode == 0:
                return True, f"Installed {len(packages)} packages"
            else:
                return False, f"Install failed: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return False, "Installation timed out after 10 minutes"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def _enable_multiarch_debian(self) -> Tuple[bool, str]:
        """Enable 32-bit support on Debian/Ubuntu"""
        try:
            # Add i386 architecture
            result = subprocess.run(
                ["sudo", "dpkg", "--add-architecture", "i386"],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False, "Failed to add i386 architecture"
            
            # Update package lists
            result = subprocess.run(
                ["sudo", "apt-get", "update"],
                capture_output=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return False, "Failed to update package lists"
            
            return True, "Multiarch enabled successfully"
        
        except Exception as e:
            return False, f"Multiarch setup error: {str(e)}"
    
    def _enable_multiarch_fedora(self) -> Tuple[bool, str]:
        """Enable 32-bit support on Fedora"""
        try:
            # Fedora uses .i686 packages, no special setup needed
            return True, "Multiarch supported via .i686 packages"
        except Exception as e:
            return False, f"Multiarch setup error: {str(e)}"
    
    def _enable_multiarch_arch(self) -> Tuple[bool, str]:
        """Enable 32-bit support on Arch"""
        pacman_conf = Path("/etc/pacman.conf")
        
        if not pacman_conf.exists():
            return False, "/etc/pacman.conf not found"
        
        try:
            with open(pacman_conf, 'r') as f:
                content = f.read()
            
            # Check if multilib already enabled
            if "[multilib]" in content and not content.split("[multilib]")[1].split("\n")[0].strip().startswith("#"):
                return True, "Multilib already enabled"
            
            return False, "Please manually enable [multilib] in /etc/pacman.conf and run 'sudo pacman -Sy'"
        
        except Exception as e:
            return False, f"Multiarch check error: {str(e)}"
    
    def _enable_multiarch_suse(self) -> Tuple[bool, str]:
        """Enable 32-bit support on openSUSE"""
        try:
            # openSUSE uses -32bit packages, no special setup needed
            return True, "Multiarch supported via -32bit packages"
        except Exception as e:
            return False, f"Multiarch setup error: {str(e)}"


def check_dependencies() -> List[str]:
    """
    Simple interface: Get list of missing dependencies
    
    Returns:
        List of missing package names
    """
    manager = DependencyManager()
    return manager.get_missing_dependencies()


def install_dependencies(skip_multiarch: bool = False) -> Tuple[bool, str]:
    """
    Simple interface: Install all dependencies
    
    Args:
        skip_multiarch: Skip multiarch setup
    
    Returns:
        Tuple of (success, message)
    """
    manager = DependencyManager()
    return manager.install_dependencies(skip_multiarch=skip_multiarch)


def verify_dependencies() -> bool:
    """
    Simple interface: Verify critical dependencies installed
    
    Returns:
        True if all critical dependencies present
    """
    manager = DependencyManager()
    return manager.verify_dependencies()


# For testing
if __name__ == "__main__":
    print("=== Dependency Manager Test ===")
    
    manager = DependencyManager()
    print(f"\nDistro: {manager.detector.distro_name}")
    print(f"Family: {manager.distro_family.value if manager.distro_family else 'unknown'}")
    print(f"Package Manager: {manager.package_manager.value if manager.package_manager else 'unknown'}")
    
    print("\n=== Checking Dependencies ===")
    missing = manager.get_missing_dependencies()
    print(f"Missing packages: {len(missing)}")
    
    if missing:
        print("\nMissing:")
        for pkg in missing[:10]:
            print(f"  - {pkg}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
    
    print("\n=== Critical Dependencies ===")
    if manager.verify_dependencies():
        print("✓ All critical dependencies installed")
    else:
        print("✗ Missing critical dependencies")
