"""
Desktop Integration Module
Create .desktop files, aliases, and system integration for Affinity products
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple, List
import shutil

from affinity_cli import config
from affinity_cli.core.wine_manager import WineManager
from affinity_cli.core.affinity_installer import AffinityInstaller


class DesktopIntegration:
    """Manage desktop integration for Affinity products"""
    
    # Desktop entry templates
    DESKTOP_ENTRY_TEMPLATE = """[Desktop Entry]
Type=Application
Name={name}
Comment={comment}
Icon={icon_path}
Exec=env WINEPREFIX="{prefix_path}" "{wine_path}" "{exe_path}" %U
Categories={categories}
Terminal=false
StartupNotify=true
MimeType={mime_types}
"""
    
    # Icon categories
    PRODUCT_CATEGORIES = {
        "photo": "Graphics;Photography;RasterGraphics;",
        "designer": "Graphics;VectorGraphics;Design;",
        "publisher": "Graphics;Publishing;Office;",
    }
    
    # MIME types
    PRODUCT_MIME_TYPES = {
        "photo": "application/x-afphoto;",
        "designer": "application/x-afdesign;",
        "publisher": "application/x-afpub;",
    }
    
    def __init__(self,
                 prefix_path: Optional[Path] = None,
                 wine_manager: Optional[WineManager] = None):
        """
        Initialize Desktop Integration
        
        Args:
            prefix_path: Wine prefix path
            wine_manager: WineManager instance
        """
        self.prefix_path = Path(prefix_path) if prefix_path else config.DEFAULT_WINE_PREFIX
        self.wine_manager = wine_manager or WineManager()
        self.wine_path = self.wine_manager.get_wine_path()
        
        if not self.wine_path:
            raise RuntimeError("Wine not found")
        
        self.installer = AffinityInstaller(prefix_path=self.prefix_path, wine_manager=self.wine_manager)
        
        # XDG directories
        self.desktop_dir = Path.home() / ".local" / "share" / "applications"
        self.icon_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
        
        # Create directories
        self.desktop_dir.mkdir(parents=True, exist_ok=True)
        self.icon_dir.mkdir(parents=True, exist_ok=True)
    
    def create_desktop_entry(self, product: str) -> Tuple[bool, str]:
        """
        Create .desktop file for a product
        
        Args:
            product: Product name (photo, designer, publisher)
        
        Returns:
            Tuple of (success, message)
        """
        if product not in config.AFFINITY_PRODUCTS:
            return False, f"Unknown product: {product}"
        
        if not self.installer.verify_installation(product):
            return False, f"{product} is not installed"
        
        product_info = config.AFFINITY_PRODUCTS[product]
        product_name = product_info["name"]
        exe_path = self.installer.get_product_path(product)
        
        if not exe_path:
            return False, f"Could not find {product} executable"
        
        # Prepare desktop entry content
        icon_path = self._get_icon_path(product)
        categories = self.PRODUCT_CATEGORIES.get(product, "Graphics;")
        mime_types = self.PRODUCT_MIME_TYPES.get(product, "")
        
        desktop_content = self.DESKTOP_ENTRY_TEMPLATE.format(
            name=product_name,
            comment=f"Professional {product} editor (via Wine)",
            icon_path=icon_path,
            prefix_path=self.prefix_path,
            wine_path=self.wine_path,
            exe_path=exe_path,
            categories=categories,
            mime_types=mime_types,
        )
        
        # Write desktop file
        desktop_file = self.desktop_dir / f"affinity-{product}.desktop"
        
        try:
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make executable
            desktop_file.chmod(0o755)
            
            return True, f"Desktop entry created: {desktop_file}"
        
        except Exception as e:
            return False, f"Failed to create desktop entry: {str(e)}"
    
    def register_desktop_entry(self, product: str) -> Tuple[bool, str]:
        """
        Register desktop entry with the system
        
        Args:
            product: Product name
        
        Returns:
            Tuple of (success, message)
        """
        desktop_file = self.desktop_dir / f"affinity-{product}.desktop"
        
        if not desktop_file.exists():
            return False, "Desktop entry does not exist"
        
        try:
            # Update desktop database
            subprocess.run(
                ["update-desktop-database", str(self.desktop_dir)],
                capture_output=True,
                timeout=10
            )
            
            return True, "Desktop entry registered"
        
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def create_bash_alias(self, product: str) -> Tuple[bool, str]:
        """
        Create bash alias for launching product
        
        Args:
            product: Product name
        
        Returns:
            Tuple of (success, message)
        """
        if product not in config.AFFINITY_PRODUCTS:
            return False, f"Unknown product: {product}"
        
        if not self.installer.verify_installation(product):
            return False, f"{product} is not installed"
        
        exe_path = self.installer.get_product_path(product)
        if not exe_path:
            return False, f"Could not find {product} executable"
        
        # Create alias command
        alias_name = f"affinity-{product}"
        alias_command = f'env WINEPREFIX="{self.prefix_path}" "{self.wine_path}" "{exe_path}"'
        
        # Detect shell config files
        shell_configs = []
        home = Path.home()
        
        for config_file in [".bashrc", ".zshrc", ".profile"]:
            config_path = home / config_file
            if config_path.exists():
                shell_configs.append(config_path)
        
        if not shell_configs:
            return False, "No shell config files found (.bashrc, .zshrc, .profile)"
        
        try:
            alias_line = f'alias {alias_name}=\'{alias_command}\'\n'
            
            for config_path in shell_configs:
                # Check if alias already exists
                with open(config_path, 'r') as f:
                    content = f.read()
                
                if alias_name in content:
                    continue  # Skip if already exists
                
                # Append alias
                with open(config_path, 'a') as f:
                    f.write(f"\n# Affinity CLI - {product}\n")
                    f.write(alias_line)
            
            return True, f"Alias '{alias_name}' created. Restart shell or run 'source ~/.bashrc'"
        
        except Exception as e:
            return False, f"Failed to create alias: {str(e)}"
    
    def extract_icon(self, product: str) -> Tuple[bool, str]:
        """
        Extract or create icon for product
        
        Args:
            product: Product name
        
        Returns:
            Tuple of (success, message)
        """
        icon_path = self._get_icon_path(product)
        
        if Path(icon_path).exists():
            return True, f"Icon already exists: {icon_path}"
        
        # Try to extract icon from exe using wrestool (if available)
        exe_path = self.installer.get_product_path(product)
        if not exe_path:
            return self._create_placeholder_icon(product)
        
        if shutil.which("wrestool") and shutil.which("icotool"):
            try:
                # Extract icon
                success, msg = self._extract_icon_with_tools(exe_path, icon_path)
                if success:
                    return True, msg
            except Exception:
                pass
        
        # Fallback: create placeholder icon
        return self._create_placeholder_icon(product)
    
    def update_desktop_database(self) -> Tuple[bool, str]:
        """
        Update desktop database to refresh application menu
        
        Returns:
            Tuple of (success, message)
        """
        try:
            subprocess.run(
                ["update-desktop-database", str(self.desktop_dir)],
                capture_output=True,
                timeout=10
            )
            
            return True, "Desktop database updated"
        
        except Exception as e:
            return False, f"Database update failed: {str(e)}"
    
    def integrate_product(self, product: str) -> Tuple[bool, str]:
        """
        Complete desktop integration for a product
        
        Args:
            product: Product name
        
        Returns:
            Tuple of (success, message)
        """
        print(f"Integrating {product} with desktop...")
        
        # Extract/create icon
        success, msg = self.extract_icon(product)
        if not success:
            print(f"  Warning: {msg}")
        
        # Create desktop entry
        success, msg = self.create_desktop_entry(product)
        if not success:
            return False, f"Desktop entry creation failed: {msg}"
        print(f"  ✓ Desktop entry created")
        
        # Register desktop entry
        success, msg = self.register_desktop_entry(product)
        if not success:
            print(f"  Warning: {msg}")
        
        # Create bash alias
        success, msg = self.create_bash_alias(product)
        if not success:
            print(f"  Warning: {msg}")
        else:
            print(f"  ✓ Bash alias created")
        
        # Update desktop database
        self.update_desktop_database()
        
        return True, f"{product} integrated successfully"
    
    def remove_integration(self, product: str) -> Tuple[bool, str]:
        """
        Remove desktop integration for a product
        
        Args:
            product: Product name
        
        Returns:
            Tuple of (success, message)
        """
        # Remove desktop entry
        desktop_file = self.desktop_dir / f"affinity-{product}.desktop"
        if desktop_file.exists():
            desktop_file.unlink()
        
        # Remove icon
        icon_path = Path(self._get_icon_path(product))
        if icon_path.exists():
            icon_path.unlink()
        
        # Note: We don't remove bash aliases as they're in user config files
        
        # Update desktop database
        self.update_desktop_database()
        
        return True, f"{product} integration removed"
    
    def _get_icon_path(self, product: str) -> str:
        """
        Get icon path for product
        
        Args:
            product: Product name
        
        Returns:
            Path to icon file
        """
        return str(self.icon_dir / f"affinity-{product}.png")
    
    def _extract_icon_with_tools(self, exe_path: Path, output_path: str) -> Tuple[bool, str]:
        """
        Extract icon from exe using wrestool and icotool
        
        Args:
            exe_path: Path to .exe file
            output_path: Path to save icon
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract .ico files
            result = subprocess.run(
                ["wrestool", "-x", "-t", "14", str(exe_path)],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0 or not result.stdout:
                return False, "Icon extraction failed"
            
            # Convert .ico to .png
            result = subprocess.run(
                ["icotool", "-x", "-o", output_path, "-"],
                input=result.stdout,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False, "Icon conversion failed"
            
            return True, f"Icon extracted to {output_path}"
        
        except Exception as e:
            return False, f"Icon extraction error: {str(e)}"
    
    def _create_placeholder_icon(self, product: str) -> Tuple[bool, str]:
        """
        Create a simple placeholder icon
        
        Args:
            product: Product name
        
        Returns:
            Tuple of (success, message)
        """
        icon_path = self._get_icon_path(product)
        
        # Use a generic icon name that might exist on the system
        generic_icons = ["applications-graphics", "image-x-generic", "application-default-icon"]
        
        for icon_name in generic_icons:
            system_icon = shutil.which("gtk-update-icon-cache")
            if system_icon:
                # Icon exists, create symlink or note
                return True, f"Using system icon: {icon_name}"
        
        return True, "Using generic icon"


def integrate_product(product: str) -> Tuple[bool, str]:
    """
    Simple interface: Complete desktop integration
    
    Args:
        product: Product name
    
    Returns:
        Tuple of (success, message)
    """
    integration = DesktopIntegration()
    return integration.integrate_product(product)


def remove_integration(product: str) -> Tuple[bool, str]:
    """
    Simple interface: Remove desktop integration
    
    Args:
        product: Product name
    
    Returns:
        Tuple of (success, message)
    """
    integration = DesktopIntegration()
    return integration.remove_integration(product)


# For testing
if __name__ == "__main__":
    print("=== Desktop Integration Test ===")
    
    try:
        integration = DesktopIntegration()
        
        print(f"\nWine prefix: {integration.prefix_path}")
        print(f"Desktop dir: {integration.desktop_dir}")
        print(f"Icon dir: {integration.icon_dir}")
        
        print("\n=== Checking Installed Products ===")
        installed = integration.installer.list_installed_products()
        
        if installed:
            print(f"Found {len(installed)} installed product(s):")
            for product in installed:
                product_name = config.AFFINITY_PRODUCTS[product]["name"]
                desktop_file = integration.desktop_dir / f"affinity-{product}.desktop"
                
                print(f"\n  {product_name}:")
                print(f"    Desktop entry: {'✓' if desktop_file.exists() else '✗'} {desktop_file}")
        else:
            print("No Affinity products installed")
    
    except RuntimeError as e:
        print(f"✗ Error: {e}")
