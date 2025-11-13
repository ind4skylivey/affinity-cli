"""
Install Command
Main orchestration for Affinity installation
"""

from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from affinity_cli import config
from affinity_cli.core.distro_detector import DistroDetector
from affinity_cli.core.dependency_manager import DependencyManager
from affinity_cli.core.wine_manager import WineManager
from affinity_cli.core.prefix_manager import PrefixManager
from affinity_cli.core.affinity_installer import AffinityInstaller
from affinity_cli.core.desktop_integration import DesktopIntegration
from affinity_cli.utils.logger import logger

console = Console()


def run_install(products: List[str],
                installer_path: Optional[str],
                wine_version: str,
                prefix_path: Optional[str],
                skip_dependencies: bool,
                skip_multiarch: bool,
                verbose: bool):
    """
    Main installation orchestration
    
    Args:
        products: List of products to install
        installer_path: Path to installer directory
        wine_version: Wine version to use
        prefix_path: Custom Wine prefix path
        skip_dependencies: Skip dependency installation
        skip_multiarch: Skip multiarch setup
        verbose: Verbose output
    """
    console.print(Panel.fit(
        "[bold cyan]Affinity CLI Installer[/bold cyan]\n"
        "This will install Affinity products on your Linux system",
        border_style="cyan"
    ))
    
    try:
        # Step 1: Detect Distribution
        console.print("\n[bold]Step 1: Detecting Linux Distribution[/bold]")
        detector = DistroDetector()
        distro_info = detector.get_distro_info()
        
        console.print(f"  • Distro: {distro_info['name']} {distro_info['version']}")
        console.print(f"  • Family: {distro_info['family']}")
        console.print(f"  • Package Manager: {distro_info['package_manager']}")
        
        # Step 2: Check/Install Dependencies
        if not skip_dependencies:
            console.print("\n[bold]Step 2: Checking System Dependencies[/bold]")
            dep_manager = DependencyManager(detector)
            
            missing = dep_manager.get_missing_dependencies()
            if missing:
                console.print(f"  • Missing {len(missing)} packages")
                
                if not Confirm.ask("  Install missing dependencies?", default=True):
                    console.print("[yellow]Skipping dependency installation[/yellow]")
                else:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console
                    ) as progress:
                        task = progress.add_task("Installing dependencies...", total=None)
                        
                        success, msg = dep_manager.install_dependencies(skip_multiarch=skip_multiarch)
                        
                        if success:
                            console.print(f"  ✓ {msg}")
                        else:
                            console.print(f"  [red]✗ {msg}[/red]")
                            return
            else:
                console.print("  ✓ All dependencies already installed")
        else:
            console.print("\n[bold]Step 2: Skipping Dependency Check[/bold]")
        
        # Step 3: Setup Wine
        console.print("\n[bold]Step 3: Setting up Wine[/bold]")
        wine_manager = WineManager(wine_version=wine_version)
        
        if wine_manager.check_wine_installed():
            console.print(f"  ✓ Wine already installed")
            wine_version_str = wine_manager.get_wine_version()
            if wine_version_str:
                console.print(f"    Version: {wine_version_str}")
        else:
            console.print(f"  • Downloading Wine {wine_manager.actual_version}...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Downloading Wine...", total=None)
                
                success, msg = wine_manager.download_wine(distro=distro_info['id'])
                
                if success:
                    console.print(f"  ✓ {msg}")
                else:
                    console.print(f"  [red]✗ {msg}[/red]")
                    return
        
        # Step 4: Create Wine Prefix
        console.print("\n[bold]Step 4: Creating Wine Prefix[/bold]")
        prefix = Path(prefix_path) if prefix_path else config.DEFAULT_WINE_PREFIX
        prefix_manager = PrefixManager(prefix_path=prefix, wine_manager=wine_manager)
        
        if prefix_manager.prefix_exists():
            console.print(f"  ✓ Wine prefix already exists at {prefix}")
        else:
            console.print(f"  • Creating prefix at {prefix}...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Creating prefix...", total=None)
                
                success, msg = prefix_manager.create_prefix()
                
                if success:
                    console.print(f"  ✓ {msg}")
                else:
                    console.print(f"  [red]✗ {msg}[/red]")
                    return
        
        # Step 5: Configure Prefix
        console.print("\n[bold]Step 5: Configuring Wine Prefix[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Configure basic settings
            task = progress.add_task("Applying optimizations...", total=None)
            success, msg = prefix_manager.configure_prefix()
            
            if not success:
                console.print(f"  [yellow]Warning: {msg}[/yellow]")
            else:
                console.print(f"  ✓ Prefix configured")
            
            # Install .NET Framework
            task = progress.add_task("Installing .NET Framework (this may take 10-15 minutes)...", total=None)
            console.print("  • Installing .NET Framework 4.8...")
            console.print("    [dim]This is required for Affinity and may take 10-15 minutes[/dim]")
            
            success, msg = prefix_manager.install_dotnet()
            
            if success:
                console.print(f"  ✓ {msg}")
            else:
                console.print(f"  [yellow]Warning: {msg}[/yellow]")
                console.print("    [dim]Affinity may not work without .NET Framework[/dim]")
            
            # Install fonts
            task = progress.add_task("Installing fonts...", total=None)
            success, msg = prefix_manager.install_fonts()
            
            if success:
                console.print(f"  ✓ Fonts installed")
            else:
                console.print(f"  [yellow]Warning: {msg}[/yellow]")
        
        # Step 6: Locate Installers
        console.print("\n[bold]Step 6: Locating Affinity Installers[/bold]")
        
        if installer_path:
            search_dir = Path(installer_path)
        else:
            # Prompt user for installer location
            default_path = str(Path.home() / "Downloads")
            installer_input = Prompt.ask(
                "  Enter path to directory containing Affinity installers",
                default=default_path
            )
            search_dir = Path(installer_input)
        
        if not search_dir.exists():
            console.print(f"  [red]✗ Directory not found: {search_dir}[/red]")
            return
        
        affinity_installer = AffinityInstaller(prefix_path=prefix, wine_manager=wine_manager)
        detected_installers = affinity_installer.detect_installer(search_dir)
        
        if not detected_installers:
            console.print(f"  [yellow]✗ No Affinity installers found in {search_dir}[/yellow]")
            console.print("\n  [dim]Please download Affinity installers from https://affinity.serif.com/[/dim]")
            return
        
        console.print(f"  ✓ Found {len(detected_installers)} installer(s):")
        for product, path in detected_installers.items():
            console.print(f"    • {config.AFFINITY_PRODUCTS[product]['name']}: {path.name}")
        
        # Determine which products to install
        if products:
            products_to_install = [p for p in products if p in detected_installers]
        else:
            products_to_install = list(detected_installers.keys())
        
        if not products_to_install:
            console.print("\n  [yellow]No products selected for installation[/yellow]")
            return
        
        # Step 7: Install Products
        console.print(f"\n[bold]Step 7: Installing Affinity Products[/bold]")
        
        installed_products = []
        for product in products_to_install:
            installer_exe = detected_installers[product]
            product_name = config.AFFINITY_PRODUCTS[product]['name']
            
            console.print(f"\n  • Installing {product_name}...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Installing {product_name}...", total=None)
                
                success, msg = affinity_installer.install_affinity_product(installer_exe, product)
                
                if success:
                    console.print(f"  ✓ {msg}")
                    installed_products.append(product)
                else:
                    console.print(f"  [red]✗ {msg}[/red]")
        
        if not installed_products:
            console.print("\n[red]No products were installed successfully[/red]")
            return
        
        # Step 8: Desktop Integration
        console.print(f"\n[bold]Step 8: Desktop Integration[/bold]")
        
        desktop_integration = DesktopIntegration(prefix_path=prefix, wine_manager=wine_manager)
        
        for product in installed_products:
            product_name = config.AFFINITY_PRODUCTS[product]['name']
            console.print(f"  • Integrating {product_name}...")
            
            success, msg = desktop_integration.integrate_product(product)
            
            if success:
                console.print(f"  ✓ {product_name} integrated")
            else:
                console.print(f"  [yellow]Warning: {msg}[/yellow]")
        
        # Step 9: Success Summary
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            "[bold green]✓ Installation Complete![/bold green]\n\n"
            f"Installed products: {', '.join([config.AFFINITY_PRODUCTS[p]['name'] for p in installed_products])}\n\n"
            "[bold]Launch from:[/bold]\n"
            "  • Application menu (search for 'Affinity')\n"
            f"  • Terminal: {', '.join([f'affinity-{p}' for p in installed_products])}\n\n"
            "[dim]Run 'affinity-cli status' to check installation[/dim]",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Installation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Installation failed: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        logger.exception("Installation failed")
