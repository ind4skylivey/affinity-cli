"""
Affinity Installer Module
Install Affinity products into Wine prefix
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import re

from affinity_cli import config
from affinity_cli.core.wine_manager import WineManager
from affinity_cli.core.prefix_manager import PrefixManager


class AffinityInstaller:
    """Install and manage Affinity products"""
    
    # Product detection patterns
    PRODUCT_PATTERNS = {
        "photo": r"(?i)photo.*\.exe",
        "designer": r"(?i)designer.*\.exe",
        "publisher": r"(?i)publisher.*\.exe",
    }
    
    def __init__(self,
                 prefix_path: Optional[Path] = None,
                 wine_manager: Optional[WineManager] = None):
        """
        Initialize Affinity Installer
        
        Args:
            prefix_path: Wine prefix path (default: ~/.wine-affinity)
            wine_manager: WineManager instance (optional)
        """
        self.prefix_path = Path(prefix_path) if prefix_path else config.DEFAULT_WINE_PREFIX
        self.wine_manager = wine_manager or WineManager()
        self.wine_path = self.wine_manager.get_wine_path()
        
        if not self.wine_path:
            raise RuntimeError("Wine not found. Install Wine first.")
        
        self.prefix_manager = PrefixManager(prefix_path=self.prefix_path, wine_manager=self.wine_manager)
    
    def detect_installer(self, search_path: Path) -> Dict[str, Optional[Path]]:
        """
        Detect Affinity installer files in a directory
        
        Args:
            search_path: Directory to search for installers
        
        Returns:
            Dictionary mapping product names to installer paths
        """
        if not search_path.exists() or not search_path.is_dir():
            return {}
        
        installers = {}
        
        # Search for .exe files
        for exe_file in search_path.glob("*.exe"):
            filename = exe_file.name
            
            # Check against patterns
            for product, pattern in self.PRODUCT_PATTERNS.items():
                if re.match(pattern, filename):
                    installers[product] = exe_file
                    break
        
        return installers
    
    def install_affinity_product(self, 
                                installer_path: Path, 
                                product: str) -> Tuple[bool, str]:
        """
        Install an Affinity product
        
        Args:
            installer_path: Path to installer .exe
            product: Product name (photo, designer, publisher)
        
        Returns:
            Tuple of (success, message)
        """
        if not installer_path.exists():
            return False, f"Installer not found: {installer_path}"
        
        if product not in config.AFFINITY_PRODUCTS:
            return False, f"Unknown product: {product}"
        
        if not self.prefix_manager.prefix_exists():
            return False, "Wine prefix does not exist. Create it first."
        
        product_name = config.AFFINITY_PRODUCTS[product]["name"]
        print(f"Installing {product_name}...")
        print(f"Installer: {installer_path}")
        print("This may take 5-10 minutes...")
        
        try:
            env = self._get_wine_env()
            
            # Silent installation flags (common for Windows installers)
            # /S = silent, /q = quiet, /qn = quiet no UI, /VERYSILENT = InnoSetup silent
            install_flags = ["/S", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]
            
            # Try installation with different flag combinations
            for flags in [install_flags, ["/S"], ["/VERYSILENT"]]:
                result = subprocess.run(
                    [str(self.wine_path), str(installer_path)] + flags,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=900  # 15 minutes
                )
                
                # Some installers return 0 even on silent mode rejection
                # Check if files were actually installed
                if self._verify_installation_files(product):
                    break
            
            # Verify installation
            if not self.verify_installation(product):
                return False, f"Installation completed but verification failed. Check {self.prefix_path}"
            
            return True, f"{product_name} installed successfully"
        
        except subprocess.TimeoutExpired:
            return False, f"{product_name} installation timed out after 15 minutes"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def verify_installation(self, product: str) -> bool:
        """
        Verify that an Affinity product is installed
        
        Args:
            product: Product name (photo, designer, publisher)
        
        Returns:
            True if product is installed and executable exists
        """
        product_path = self.get_product_path(product)
        return product_path is not None and product_path.exists()
    
    def get_product_path(self, product: str) -> Optional[Path]:
        """
        Get path to installed product executable
        
        Args:
            product: Product name (photo, designer, publisher)
        
        Returns:
            Path to product .exe or None if not found
        """
        if product not in config.AFFINITY_PRODUCTS:
            return None
        
        product_info = config.AFFINITY_PRODUCTS[product]
        install_path = product_info["install_path"]
        exe_name = product_info["exe_name"]
        
        # Check common installation locations
        possible_paths = [
            self.prefix_path / "drive_c" / install_path / exe_name,
            self.prefix_path / "drive_c" / "Program Files" / "Affinity" / product.capitalize() / exe_name,
            self.prefix_path / "drive_c" / "Program Files (x86)" / "Affinity" / product.capitalize() / exe_name,
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Search recursively as fallback
        affinity_dir = self.prefix_path / "drive_c" / "Program Files" / "Affinity"
        if affinity_dir.exists():
            for exe_path in affinity_dir.rglob(exe_name):
                return exe_path
        
        return None
    
    def list_installed_products(self) -> List[str]:
        """
        List all installed Affinity products
        
        Returns:
            List of installed product names
        """
        installed = []
        
        for product in config.AFFINITY_PRODUCTS.keys():
            if self.verify_installation(product):
                installed.append(product)
        
        return installed
    
    def launch_product(self, product: str) -> Tuple[bool, str]:
        """
        Launch an installed Affinity product
        
        Args:
            product: Product name (photo, designer, publisher)
        
        Returns:
            Tuple of (success, message)
        """
        if not self.verify_installation(product):
            return False, f"{product} is not installed"
        
        product_path = self.get_product_path(product)
        if not product_path:
            return False, f"Could not find {product} executable"
        
        try:
            env = self._get_wine_env()
            
            # Launch in background
            subprocess.Popen(
                [str(self.wine_path), str(product_path)],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            product_name = config.AFFINITY_PRODUCTS[product]["name"]
            return True, f"Launched {product_name}"
        
        except Exception as e:
            return False, f"Launch error: {str(e)}"
    
    def uninstall_product(self, product: str) -> Tuple[bool, str]:
        """
        Uninstall an Affinity product
        
        Args:
            product: Product name (photo, designer, publisher)
        
        Returns:
            Tuple of (success, message)
        """
        if not self.verify_installation(product):
            return False, f"{product} is not installed"
        
        # Find uninstaller
        uninstall_paths = [
            self.prefix_path / "drive_c" / config.AFFINITY_PRODUCTS[product]["install_path"] / "unins000.exe",
            self.prefix_path / "drive_c" / "Program Files" / "Affinity" / product.capitalize() / "uninstall.exe",
        ]
        
        uninstaller = None
        for path in uninstall_paths:
            if path.exists():
                uninstaller = path
                break
        
        if not uninstaller:
            return False, f"Uninstaller not found for {product}"
        
        try:
            env = self._get_wine_env()
            
            result = subprocess.run(
                [str(self.wine_path), str(uninstaller), "/VERYSILENT", "/NORESTART"],
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            product_name = config.AFFINITY_PRODUCTS[product]["name"]
            return True, f"{product_name} uninstalled successfully"
        
        except subprocess.TimeoutExpired:
            return False, "Uninstallation timed out"
        except Exception as e:
            return False, f"Uninstall error: {str(e)}"
    
    def _verify_installation_files(self, product: str) -> bool:
        """
        Check if product files exist (for installation verification)
        
        Args:
            product: Product name
        
        Returns:
            True if installation files are present
        """
        product_path = self.get_product_path(product)
        return product_path is not None and product_path.exists()
    
    def _get_wine_env(self) -> Dict[str, str]:
        """
        Get environment variables for Wine execution
        
        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()
        env["WINEPREFIX"] = str(self.prefix_path)
        env["WINEDEBUG"] = "-all"
        env["WINEARCH"] = "win64"
        
        # Add Wine bin to PATH
        wine_bin_dir = self.wine_path.parent
        env["PATH"] = f"{wine_bin_dir}:{env.get('PATH', '')}"
        
        return env


def detect_installers(search_path: Path) -> Dict[str, Optional[Path]]:
    """
    Simple interface: Detect Affinity installers
    
    Args:
        search_path: Directory to search
    
    Returns:
        Dictionary of product -> installer path
    """
    installer = AffinityInstaller()
    return installer.detect_installer(search_path)


def install_product(installer_path: Path, product: str) -> Tuple[bool, str]:
    """
    Simple interface: Install Affinity product
    
    Args:
        installer_path: Path to installer .exe
        product: Product name
    
    Returns:
        Tuple of (success, message)
    """
    installer = AffinityInstaller()
    return installer.install_affinity_product(installer_path, product)


def list_installed() -> List[str]:
    """
    Simple interface: List installed products
    
    Returns:
        List of installed product names
    """
    installer = AffinityInstaller()
    return installer.list_installed_products()


# For testing
if __name__ == "__main__":
    print("=== Affinity Installer Test ===")
    
    try:
        installer = AffinityInstaller()
        
        print(f"\nWine prefix: {installer.prefix_path}")
        print(f"Wine path: {installer.wine_path}")
        
        print("\n=== Checking Installed Products ===")
        installed = installer.list_installed_products()
        
        if installed:
            print(f"Found {len(installed)} installed product(s):")
            for product in installed:
                product_name = config.AFFINITY_PRODUCTS[product]["name"]
                product_path = installer.get_product_path(product)
                print(f"  ✓ {product_name}")
                print(f"    Path: {product_path}")
        else:
            print("No Affinity products installed yet")
    
    except RuntimeError as e:
        print(f"✗ Error: {e}")
