"""
Status Command
Check installation status and system information
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from affinity_cli import config
from affinity_cli.core.distro_detector import DistroDetector
from affinity_cli.core.dependency_manager import DependencyManager
from affinity_cli.core.wine_manager import WineManager
from affinity_cli.core.prefix_manager import PrefixManager
from affinity_cli.core.affinity_installer import AffinityInstaller

console = Console()


def run_status(verbose: bool = False):
    """
    Display installation status
    
    Args:
        verbose: Show detailed information
    """
    console.print(Panel.fit(
        "[bold cyan]Affinity CLI - System Status[/bold cyan]",
        border_style="cyan"
    ))
    
    # System Information
    console.print("\n[bold]System Information[/bold]")
    detector = DistroDetector()
    distro_info = detector.get_distro_info()
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="cyan")
    table.add_column("Value")
    
    table.add_row("Distribution", f"{distro_info['name']} {distro_info['version']}")
    table.add_row("Family", distro_info['family'])
    table.add_row("Package Manager", distro_info['package_manager'])
    
    console.print(table)
    
    # Dependencies Status
    console.print("\n[bold]Dependencies Status[/bold]")
    dep_manager = DependencyManager(detector)
    
    if dep_manager.verify_dependencies():
        console.print("  ✓ All critical dependencies installed")
    else:
        console.print("  [yellow]✗ Some critical dependencies missing[/yellow]")
    
    if verbose:
        missing = dep_manager.get_missing_dependencies()
        if missing:
            console.print(f"\n  Missing packages ({len(missing)}):")
            for pkg in missing[:10]:
                console.print(f"    • {pkg}")
            if len(missing) > 10:
                console.print(f"    ... and {len(missing) - 10} more")
    
    # Wine Status
    console.print("\n[bold]Wine Status[/bold]")
    wine_manager = WineManager()
    
    if wine_manager.check_wine_installed():
        console.print(f"  ✓ Wine installed at {wine_manager.wine_dir}")
        version = wine_manager.get_wine_version()
        if version:
            console.print(f"    Version: {version}")
    else:
        console.print("  [yellow]✗ Wine not installed[/yellow]")
        console.print(f"    Expected at: {wine_manager.wine_bin}")
    
    # Wine Prefix Status
    console.print("\n[bold]Wine Prefix Status[/bold]")
    prefix_manager = PrefixManager()
    
    if prefix_manager.prefix_exists():
        console.print(f"  ✓ Prefix exists at {prefix_manager.prefix_path}")
        
        if verbose:
            # Check for .NET
            dotnet_path = prefix_manager.prefix_path / "drive_c" / "windows" / "Microsoft.NET"
            if dotnet_path.exists():
                console.print("    ✓ .NET Framework installed")
            else:
                console.print("    [yellow]✗ .NET Framework not detected[/yellow]")
    else:
        console.print(f"  [yellow]✗ Prefix does not exist[/yellow]")
        console.print(f"    Expected at: {prefix_manager.prefix_path}")
    
    # Installed Products
    console.print("\n[bold]Installed Affinity Products[/bold]")
    
    try:
        affinity_installer = AffinityInstaller()
        installed = affinity_installer.list_installed_products()
        
        if installed:
            for product in installed:
                product_name = config.AFFINITY_PRODUCTS[product]['name']
                product_path = affinity_installer.get_product_path(product)
                
                console.print(f"  ✓ {product_name}")
                if verbose and product_path:
                    console.print(f"    Path: {product_path}")
        else:
            console.print("  [yellow]No Affinity products installed[/yellow]")
    
    except RuntimeError:
        console.print("  [yellow]Cannot check (Wine not installed)[/yellow]")
    
    # Desktop Integration
    console.print("\n[bold]Desktop Integration[/bold]")
    
    desktop_dir = config.HOME_DIR / ".local" / "share" / "applications"
    desktop_files_found = []
    
    for product in config.AFFINITY_PRODUCTS.keys():
        desktop_file = desktop_dir / f"affinity-{product}.desktop"
        if desktop_file.exists():
            desktop_files_found.append(product)
    
    if desktop_files_found:
        console.print(f"  ✓ {len(desktop_files_found)} desktop entry(ies) found")
        for product in desktop_files_found:
            product_name = config.AFFINITY_PRODUCTS[product]['name']
            console.print(f"    • {product_name}")
    else:
        console.print("  [yellow]No desktop entries found[/yellow]")
    
    # Configuration
    if verbose:
        console.print("\n[bold]Configuration[/bold]")
        console.print(f"  Config dir: {config.CONFIG_DIR}")
        console.print(f"  Cache dir: {config.CACHE_DIR}")
        console.print(f"  Wine prefix: {config.DEFAULT_WINE_PREFIX}")
        console.print(f"  Wine install: {config.DEFAULT_WINE_INSTALL}")
    
    console.print()
