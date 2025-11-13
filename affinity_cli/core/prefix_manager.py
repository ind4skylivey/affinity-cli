"""
Prefix Manager Module
Create and configure Wine prefix for Affinity products
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple, Dict
import tempfile

from affinity_cli import config
from affinity_cli.core.wine_manager import WineManager


class PrefixManager:
    """Manage Wine prefix creation and configuration"""
    
    def __init__(self, 
                 prefix_path: Optional[Path] = None,
                 wine_manager: Optional[WineManager] = None):
        """
        Initialize Prefix Manager
        
        Args:
            prefix_path: Path to Wine prefix (default: ~/.wine-affinity)
            wine_manager: WineManager instance (optional)
        """
        self.prefix_path = Path(prefix_path) if prefix_path else config.DEFAULT_WINE_PREFIX
        self.wine_manager = wine_manager or WineManager()
        self.wine_path = self.wine_manager.get_wine_path()
        
        if not self.wine_path:
            raise RuntimeError("Wine not found. Install Wine first.")
    
    def prefix_exists(self) -> bool:
        """
        Check if Wine prefix exists
        
        Returns:
            True if prefix directory exists and is valid
        """
        if not self.prefix_path.exists():
            return False
        
        # Check for key Wine prefix directories
        system32 = self.prefix_path / "drive_c" / "windows" / "system32"
        return system32.exists()
    
    def create_prefix(self) -> Tuple[bool, str]:
        """
        Create a new Wine prefix
        
        Returns:
            Tuple of (success, message)
        """
        if self.prefix_exists():
            return True, f"Prefix already exists at {self.prefix_path}"
        
        print(f"Creating Wine prefix at {self.prefix_path}...")
        
        try:
            # Create prefix directory
            self.prefix_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize Wine prefix
            env = self._get_wine_env()
            
            result = subprocess.run(
                [str(self.wine_path), "wineboot", "--init"],
                env=env,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return False, f"Prefix creation failed: {result.stderr}"
            
            # Wait for wineserver to finish
            subprocess.run(
                [str(self.wine_path.parent / "wineserver"), "-w"],
                env=env,
                timeout=60
            )
            
            if not self.prefix_exists():
                return False, "Prefix creation succeeded but validation failed"
            
            return True, f"Prefix created at {self.prefix_path}"
        
        except subprocess.TimeoutExpired:
            return False, "Prefix creation timed out"
        except Exception as e:
            return False, f"Prefix creation error: {str(e)}"
    
    def configure_prefix(self) -> Tuple[bool, str]:
        """
        Configure Wine prefix with optimal settings for Affinity
        
        Returns:
            Tuple of (success, message)
        """
        if not self.prefix_exists():
            return False, "Prefix does not exist. Create it first."
        
        print("Configuring Wine prefix...")
        
        try:
            # Set Windows version
            success, msg = self.set_windows_version("win10")
            if not success:
                return False, f"Windows version setup failed: {msg}"
            
            # Apply registry tweaks
            success, msg = self.optimize_prefix()
            if not success:
                return False, f"Optimization failed: {msg}"
            
            return True, "Prefix configured successfully"
        
        except Exception as e:
            return False, f"Configuration error: {str(e)}"
    
    def install_dotnet(self) -> Tuple[bool, str]:
        """
        Install .NET Framework 4.8 using winetricks
        
        Returns:
            Tuple of (success, message)
        """
        if not self.prefix_exists():
            return False, "Prefix does not exist"
        
        winetricks = self._find_winetricks()
        if not winetricks:
            return False, "winetricks not found. Install it first."
        
        print("Installing .NET Framework 4.8 (this may take 10-15 minutes)...")
        
        try:
            env = self._get_wine_env()
            
            result = subprocess.run(
                [winetricks, "-q", "dotnet48"],
                env=env,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode != 0:
                return False, f".NET installation failed: {result.stderr}"
            
            return True, ".NET Framework 4.8 installed successfully"
        
        except subprocess.TimeoutExpired:
            return False, ".NET installation timed out after 30 minutes"
        except Exception as e:
            return False, f".NET installation error: {str(e)}"
    
    def install_fonts(self) -> Tuple[bool, str]:
        """
        Install core fonts using winetricks
        
        Returns:
            Tuple of (success, message)
        """
        if not self.prefix_exists():
            return False, "Prefix does not exist"
        
        winetricks = self._find_winetricks()
        if not winetricks:
            return False, "winetricks not found"
        
        print("Installing fonts...")
        
        fonts = ["corefonts", "tahoma"]
        
        try:
            env = self._get_wine_env()
            
            for font in fonts:
                print(f"  Installing {font}...")
                result = subprocess.run(
                    [winetricks, "-q", font],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    print(f"  Warning: {font} installation failed")
            
            return True, "Fonts installed successfully"
        
        except subprocess.TimeoutExpired:
            return False, "Font installation timed out"
        except Exception as e:
            return False, f"Font installation error: {str(e)}"
    
    def set_windows_version(self, version: str = "win10") -> Tuple[bool, str]:
        """
        Set Windows version for the prefix
        
        Args:
            version: Windows version (win10, win11, win8, win7)
        
        Returns:
            Tuple of (success, message)
        """
        if not self.prefix_exists():
            return False, "Prefix does not exist"
        
        try:
            env = self._get_wine_env()
            
            # Use winecfg to set version
            # This is non-interactive when setting via registry
            reg_commands = [
                f'[HKEY_CURRENT_USER\\Software\\Wine]',
                f'"Version"="{version}"',
            ]
            
            success, msg = self._apply_registry_tweaks(reg_commands)
            if not success:
                return False, f"Registry update failed: {msg}"
            
            return True, f"Windows version set to {version}"
        
        except Exception as e:
            return False, f"Version setting error: {str(e)}"
    
    def optimize_prefix(self) -> Tuple[bool, str]:
        """
        Apply performance and compatibility optimizations
        
        Returns:
            Tuple of (success, message)
        """
        if not self.prefix_exists():
            return False, "Prefix does not exist"
        
        print("Applying optimizations...")
        
        # Registry tweaks for Affinity
        reg_tweaks = [
            # Disable Wine debug output
            'REGEDIT4',
            '',
            '[HKEY_CURRENT_USER\\Software\\Wine\\Debug]',
            '"LogLevel"=dword:00000000',
            '',
            # Enable CSMT (multithreaded graphics)
            '[HKEY_CURRENT_USER\\Software\\Wine\\Direct3D]',
            '"csmt"=dword:00000001',
            '"MaxVersionGL"=dword:00040006',
            '',
            # DPI settings (96 = 100%, 192 = 200%)
            '[HKEY_CURRENT_USER\\Control Panel\\Desktop]',
            '"LogPixels"=dword:00000060',
            '',
            # Disable crash dialogs
            '[HKEY_CURRENT_USER\\Software\\Wine\\WineDbg]',
            '"ShowCrashDialog"=dword:00000000',
        ]
        
        try:
            success, msg = self._apply_registry_tweaks(reg_tweaks)
            if not success:
                return False, f"Registry tweaks failed: {msg}"
            
            return True, "Optimizations applied successfully"
        
        except Exception as e:
            return False, f"Optimization error: {str(e)}"
    
    def backup_prefix(self, backup_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Create backup of Wine prefix
        
        Args:
            backup_path: Path to save backup (default: prefix_path.backup)
        
        Returns:
            Tuple of (success, message)
        """
        if not self.prefix_exists():
            return False, "Prefix does not exist"
        
        backup_path = backup_path or Path(str(self.prefix_path) + ".backup")
        
        try:
            import shutil
            
            print(f"Backing up prefix to {backup_path}...")
            
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            shutil.copytree(self.prefix_path, backup_path)
            
            return True, f"Backup created at {backup_path}"
        
        except Exception as e:
            return False, f"Backup error: {str(e)}"
    
    def _get_wine_env(self) -> Dict[str, str]:
        """
        Get environment variables for Wine execution
        
        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()
        env["WINEPREFIX"] = str(self.prefix_path)
        env["WINEDEBUG"] = "-all"  # Disable debug output
        env["WINEARCH"] = "win64"   # 64-bit architecture
        
        # Add Wine bin to PATH
        wine_bin_dir = self.wine_path.parent
        env["PATH"] = f"{wine_bin_dir}:{env.get('PATH', '')}"
        
        return env
    
    def _find_winetricks(self) -> Optional[str]:
        """
        Find winetricks executable
        
        Returns:
            Path to winetricks or None
        """
        import shutil
        return shutil.which("winetricks")
    
    def _apply_registry_tweaks(self, reg_lines: list) -> Tuple[bool, str]:
        """
        Apply registry tweaks to Wine prefix
        
        Args:
            reg_lines: List of registry file lines
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create temporary .reg file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False) as f:
                reg_file = Path(f.name)
                f.write('\n'.join(reg_lines))
            
            # Apply registry file
            env = self._get_wine_env()
            
            result = subprocess.run(
                [str(self.wine_path), "regedit", str(reg_file)],
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            reg_file.unlink()
            
            if result.returncode != 0:
                return False, f"regedit failed: {result.stderr}"
            
            return True, "Registry tweaks applied"
        
        except Exception as e:
            return False, f"Registry error: {str(e)}"


def create_prefix(prefix_path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Simple interface: Create Wine prefix
    
    Args:
        prefix_path: Path to prefix directory
    
    Returns:
        Tuple of (success, message)
    """
    manager = PrefixManager(prefix_path=prefix_path)
    return manager.create_prefix()


def configure_prefix(prefix_path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Simple interface: Configure Wine prefix
    
    Args:
        prefix_path: Path to prefix directory
    
    Returns:
        Tuple of (success, message)
    """
    manager = PrefixManager(prefix_path=prefix_path)
    return manager.configure_prefix()


# For testing
if __name__ == "__main__":
    print("=== Prefix Manager Test ===")
    
    try:
        manager = PrefixManager()
        
        print(f"\nPrefix path: {manager.prefix_path}")
        print(f"Wine path: {manager.wine_path}")
        
        print("\n=== Checking Prefix ===")
        if manager.prefix_exists():
            print(f"✓ Prefix exists at {manager.prefix_path}")
        else:
            print(f"✗ Prefix does not exist")
            print(f"  Expected at: {manager.prefix_path}")
    
    except RuntimeError as e:
        print(f"✗ Error: {e}")
