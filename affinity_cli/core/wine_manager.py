"""
Wine Manager Module
Download, install, and manage ElementalWarrior Wine fork for Affinity
"""

import subprocess
import hashlib
import urllib.request
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict
import json

from affinity_cli import config


class WineManager:
    """Manage Wine installation and configuration"""
    
    # ElementalWarrior Wine versions and download URLs
    WINE_VERSIONS = {
        "latest": {
            "version": "9.20-staging",
            "urls": {
                "ubuntu": "https://github.com/Kron4ek/Wine-Builds/releases/download/9.20-staging/wine-9.20-staging-amd64.tar.xz",
                "debian": "https://github.com/Kron4ek/Wine-Builds/releases/download/9.20-staging/wine-9.20-staging-amd64.tar.xz",
                "fedora": "https://github.com/Kron4ek/Wine-Builds/releases/download/9.20-staging/wine-9.20-staging-amd64.tar.xz",
                "arch": "https://github.com/Kron4ek/Wine-Builds/releases/download/9.20-staging/wine-9.20-staging-amd64.tar.xz",
                "generic": "https://github.com/Kron4ek/Wine-Builds/releases/download/9.20-staging/wine-9.20-staging-amd64.tar.xz",
            },
        },
    }
    
    def __init__(self, wine_version: str = "latest", install_dir: Optional[Path] = None):
        """
        Initialize Wine Manager
        
        Args:
            wine_version: Wine version to use (default: "latest")
            install_dir: Custom installation directory (default: ~/.local/wine)
        """
        self.wine_version = wine_version
        self.install_dir = Path(install_dir) if install_dir else config.DEFAULT_WINE_INSTALL
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
        self.version_info = self.WINE_VERSIONS.get(wine_version, self.WINE_VERSIONS["latest"])
        self.actual_version = self.version_info["version"]
        
        self.wine_dir = self.install_dir / f"wine-{self.actual_version}"
        self.wine_bin = self.wine_dir / "bin" / "wine64"
    
    def check_wine_installed(self) -> bool:
        """
        Check if Wine is already installed
        
        Returns:
            True if Wine binary exists and is executable
        """
        return self.wine_bin.exists() and self.wine_bin.is_file()
    
    def get_wine_path(self) -> Optional[Path]:
        """
        Get path to Wine binary
        
        Returns:
            Path to wine64 binary if installed, None otherwise
        """
        if self.check_wine_installed():
            return self.wine_bin
        
        # Check system wine as fallback
        system_wine = shutil.which("wine64") or shutil.which("wine")
        if system_wine:
            return Path(system_wine)
        
        return None
    
    def download_wine(self, distro: str = "generic") -> Tuple[bool, str]:
        """
        Download Wine for the specified distro
        
        Args:
            distro: Distribution name (ubuntu, fedora, arch, etc.)
        
        Returns:
            Tuple of (success, message or error)
        """
        if self.check_wine_installed():
            return True, f"Wine already installed at {self.wine_dir}"
        
        # Get download URL
        distro_urls = self.version_info.get("urls", {})
        url = distro_urls.get(distro.lower(), distro_urls.get("generic"))
        
        if not url:
            return False, f"No Wine download URL for distro: {distro}"
        
        # Download to cache
        cache_dir = config.CACHE_DIR / "wine"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        filename = url.split("/")[-1]
        download_path = cache_dir / filename
        
        try:
            # Check if already downloaded
            if download_path.exists():
                print(f"Using cached Wine: {download_path}")
            else:
                print(f"Downloading Wine from {url}...")
                success, msg = self._download_file(url, download_path)
                if not success:
                    return False, f"Download failed: {msg}"
            
            # Extract archive
            print(f"Extracting Wine to {self.install_dir}...")
            success, msg = self._extract_archive(download_path, self.install_dir)
            if not success:
                return False, f"Extraction failed: {msg}"
            
            # Verify installation
            if not self.check_wine_installed():
                return False, "Wine binary not found after extraction"
            
            # Make executable
            self.wine_bin.chmod(0o755)
            
            return True, f"Wine {self.actual_version} installed successfully"
        
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def verify_wine_integrity(self, file_path: Path) -> bool:
        """
        Verify Wine archive integrity (placeholder for SHA256 verification)
        
        Args:
            file_path: Path to downloaded archive
        
        Returns:
            True if integrity check passes
        """
        # TODO: Implement SHA256 checksum verification
        # For now, just check file exists and has reasonable size
        if not file_path.exists():
            return False
        
        file_size = file_path.stat().st_size
        if file_size < 10_000_000:  # Less than 10MB is suspicious
            return False
        
        return True
    
    def setup_wine_binary(self) -> Tuple[bool, str]:
        """
        Setup Wine binary and create symlinks
        
        Returns:
            Tuple of (success, message)
        """
        if not self.check_wine_installed():
            return False, "Wine not installed"
        
        try:
            # Create wine64 symlink if needed
            wine_link = self.wine_dir / "bin" / "wine"
            wine64_bin = self.wine_dir / "bin" / "wine64"
            
            if not wine_link.exists() and wine64_bin.exists():
                wine_link.symlink_to(wine64_bin)
            
            # Add to PATH (optional, user can do this manually)
            # We return the path for user to add to their shell rc
            
            return True, f"Wine setup complete at {self.wine_dir}"
        
        except Exception as e:
            return False, f"Setup error: {str(e)}"
    
    def get_wine_version(self) -> Optional[str]:
        """
        Get installed Wine version
        
        Returns:
            Version string or None if not installed
        """
        wine_path = self.get_wine_path()
        if not wine_path:
            return None
        
        try:
            result = subprocess.run(
                [str(wine_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
        except Exception:
            pass
        
        return None
    
    def _download_file(self, url: str, destination: Path, chunk_size: int = 8192) -> Tuple[bool, str]:
        """
        Download file from URL with progress
        
        Args:
            url: URL to download from
            destination: Path to save file
            chunk_size: Download chunk size in bytes
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(destination, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Simple progress indicator
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='\r')
                
                print()  # New line after progress
                return True, f"Downloaded {downloaded} bytes"
        
        except Exception as e:
            return False, f"Download error: {str(e)}"
    
    def _extract_archive(self, archive_path: Path, destination: Path) -> Tuple[bool, str]:
        """
        Extract tar.xz archive
        
        Args:
            archive_path: Path to archive file
            destination: Directory to extract to
        
        Returns:
            Tuple of (success, message)
        """
        try:
            import tarfile
            
            with tarfile.open(archive_path, 'r:xz') as tar:
                tar.extractall(path=destination)
            
            return True, f"Extracted to {destination}"
        
        except ImportError:
            # Fallback to tar command
            try:
                result = subprocess.run(
                    ["tar", "-xJf", str(archive_path), "-C", str(destination)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    return True, f"Extracted to {destination}"
                else:
                    return False, f"Extraction failed: {result.stderr}"
            
            except Exception as e:
                return False, f"Extraction error: {str(e)}"
        
        except Exception as e:
            return False, f"Extraction error: {str(e)}"


def check_wine_installed(wine_version: str = "latest") -> bool:
    """
    Simple interface: Check if Wine is installed
    
    Args:
        wine_version: Wine version to check
    
    Returns:
        True if Wine is installed
    """
    manager = WineManager(wine_version=wine_version)
    return manager.check_wine_installed()


def download_wine(wine_version: str = "latest", distro: str = "generic") -> Tuple[bool, str]:
    """
    Simple interface: Download and install Wine
    
    Args:
        wine_version: Wine version to download
        distro: Distribution name
    
    Returns:
        Tuple of (success, message)
    """
    manager = WineManager(wine_version=wine_version)
    return manager.download_wine(distro=distro)


def get_wine_path(wine_version: str = "latest") -> Optional[Path]:
    """
    Simple interface: Get Wine binary path
    
    Args:
        wine_version: Wine version
    
    Returns:
        Path to wine64 binary or None
    """
    manager = WineManager(wine_version=wine_version)
    return manager.get_wine_path()


# For testing
if __name__ == "__main__":
    print("=== Wine Manager Test ===")
    
    manager = WineManager()
    
    print(f"\nWine version: {manager.actual_version}")
    print(f"Install directory: {manager.install_dir}")
    print(f"Wine binary path: {manager.wine_bin}")
    
    print("\n=== Checking Wine Installation ===")
    if manager.check_wine_installed():
        print(f"✓ Wine installed at {manager.wine_dir}")
        version = manager.get_wine_version()
        if version:
            print(f"  Version: {version}")
    else:
        print("✗ Wine not installed")
        print(f"  Expected at: {manager.wine_bin}")
    
    wine_path = manager.get_wine_path()
    if wine_path:
        print(f"\nWine executable: {wine_path}")
    else:
        print("\nNo Wine found (neither custom nor system)")
