"""
Wine Manager Module
Download, install, and manage ElementalWarrior Wine fork for Affinity
"""

import os
import subprocess
import hashlib
import tarfile
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
            "version": "10.18-staging",
            "urls": {
                "ubuntu": "https://github.com/Kron4ek/Wine-Builds/releases/download/10.18/wine-10.18-staging-amd64-wow64.tar.xz",
                "debian": "https://github.com/Kron4ek/Wine-Builds/releases/download/10.18/wine-10.18-staging-amd64-wow64.tar.xz",
                "fedora": "https://github.com/Kron4ek/Wine-Builds/releases/download/10.18/wine-10.18-staging-amd64-wow64.tar.xz",
                "arch": "https://github.com/Kron4ek/Wine-Builds/releases/download/10.18/wine-10.18-staging-amd64-wow64.tar.xz",
                "generic": "https://github.com/Kron4ek/Wine-Builds/releases/download/10.18/wine-10.18-staging-amd64-wow64.tar.xz",
            },
            "checksum": {
                "type": "sha256",
                "source": "https://github.com/Kron4ek/Wine-Builds/releases/download/10.18/sha256sums.txt",
                "filename": "wine-10.18-staging-amd64-wow64.tar.xz",
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
        
        self._refresh_wine_paths()
    
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
                if not self.verify_wine_integrity(download_path):
                    print("Cached Wine archive failed integrity check. Re-downloading...")
                    download_path.unlink(missing_ok=True)

            if not download_path.exists():
                print(f"Downloading Wine from {url}...")
                success, msg = self._download_file(url, download_path)
                if not success:
                    return False, f"Download failed: {msg}"

            if not self.verify_wine_integrity(download_path):
                download_path.unlink(missing_ok=True)
                return False, "Failed to verify Wine archive integrity"

            # Extract archive
            print(f"Extracting Wine to {self.install_dir}...")
            success, msg = self._extract_archive(download_path, self.install_dir)
            if not success:
                return False, f"Extraction failed: {msg}"
            
            # Refresh paths (archives may include architecture suffixes)
            self._refresh_wine_paths()

            # Verify installation
            if not self.check_wine_installed():
                return False, "Wine binary not found after extraction"
            
            # Make executable
            self.wine_bin.chmod(0o755)
            
            return True, f"Wine {self.actual_version} installed successfully"
        
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _refresh_wine_paths(self):
        """Update wine_dir and wine_bin to point at the installed version"""
        expected = self.install_dir / f"wine-{self.actual_version}"
        if expected.exists():
            self.wine_dir = expected
        else:
            candidates = sorted(self.install_dir.glob(f"wine-{self.actual_version}*"))
            for candidate in candidates:
                if candidate.is_dir():
                    self.wine_dir = candidate
                    break
            else:
                self.wine_dir = expected
        wine64 = self.wine_dir / "bin" / "wine64"
        if wine64.exists():
            self.wine_bin = wine64
        else:
            self.wine_bin = self.wine_dir / "bin" / "wine"
    
    def verify_wine_integrity(self, file_path: Path) -> bool:
        """
        Verify Wine archive integrity using SHA256 checksums

        Args:
            file_path: Path to downloaded archive

        Returns:
            True if integrity check passes
        """
        if not file_path.exists():
            return False

        expected_checksum = self._get_expected_checksum(file_path)
        if not expected_checksum:
            return False

        actual_checksum = self._calculate_sha256(file_path)
        return actual_checksum == expected_checksum
    
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
        Extract tar.xz archive using a path-safe routine

        Args:
            archive_path: Path to archive file
            destination: Directory to extract to

        Returns:
            Tuple of (success, message)
        """
        try:
            with tarfile.open(archive_path, 'r:*') as tar:
                self._safe_extract(tar, destination)

            return True, f"Extracted to {destination}"

        except (tarfile.TarError, OSError, ValueError) as e:
            self._cleanup_partial_install()
            return False, f"Extraction error: {str(e)}"

    def _safe_extract(self, tar: tarfile.TarFile, destination: Path) -> None:
        """Safely extract archive members within destination"""
        destination_path = Path(destination).resolve()
        destination_path.mkdir(parents=True, exist_ok=True)

        dest_str = str(destination_path)

        safe_members = []

        for member in tar.getmembers():
            if member.name is None:
                continue

            member_path = destination_path / member.name
            resolved_path = member_path.resolve()
            resolved_str = str(resolved_path)
            if not (resolved_str == dest_str or resolved_str.startswith(dest_str + os.sep)):
                raise ValueError(f"Archive member escapes destination: {member.name}")

            if member.ischr() or member.isblk() or member.isfifo() or member.isdev():
                raise ValueError(f"Archive contains unsupported special file: {member.name}")

            if member.islnk() or member.issym():
                link_target = Path(member.linkname)
                if link_target.is_absolute():
                    raise ValueError(f"Archive contains unsafe link: {member.name}")

                target_path = (member_path.parent / link_target).resolve()
                target_str = str(target_path)
                if ".." in link_target.parts or not (target_str == dest_str or target_str.startswith(dest_str + os.sep)):
                    raise ValueError(f"Archive contains escaping link: {member.name}")

            safe_members.append(member)

        tar.extractall(path=str(destination_path), members=safe_members)

    def _cleanup_partial_install(self) -> None:
        """Remove a partially extracted Wine directory"""
        if self.wine_dir.exists():
            shutil.rmtree(self.wine_dir, ignore_errors=True)

    def _calculate_sha256(self, file_path: Path, chunk_size: int = 1024 * 1024) -> str:
        """Compute SHA256 checksum for a file"""
        digest = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    def _get_expected_checksum(self, file_path: Path) -> Optional[str]:
        """Retrieve the expected checksum for a downloaded archive"""
        checksum_info: Optional[Dict[str, str]] = self.version_info.get("checksum")
        if not checksum_info:
            return None

        if checksum_info.get("sha256"):
            return checksum_info["sha256"]

        source_url = checksum_info.get("source")
        if not source_url:
            return None

        checksum_file = self._ensure_checksum_file(source_url)
        if not checksum_file:
            return None

        expected_filename = checksum_info.get("filename") or file_path.name
        return self._parse_checksum_file(checksum_file, expected_filename)

    def _ensure_checksum_file(self, url: str) -> Optional[Path]:
        """Download (and cache) a checksum file"""
        checksum_dir = config.CACHE_DIR / "checksums"
        checksum_dir.mkdir(parents=True, exist_ok=True)
        checksum_path = checksum_dir / Path(url).name

        if not checksum_path.exists():
            success, _ = self._download_file(url, checksum_path)
            if not success:
                return None

        return checksum_path

    def _parse_checksum_file(self, checksum_file: Path, target_filename: str) -> Optional[str]:
        """Extract the checksum for a specific filename from a checksum list"""
        try:
            with open(checksum_file, 'r', encoding='utf-8') as handle:
                for line in handle:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if len(parts) < 2:
                        continue

                    checksum, *name_parts = parts
                    candidate_name = " ".join(name_parts).lstrip('*')
                    if candidate_name.endswith(target_filename):
                        return checksum
        except OSError:
            return None

        return None


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
