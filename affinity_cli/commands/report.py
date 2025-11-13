"""
Report Command
Generate system report for troubleshooting
"""

from typing import Optional
from pathlib import Path
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

from affinity_cli import __version__, config
from affinity_cli.core.distro_detector import DistroDetector
from affinity_cli.core.dependency_manager import DependencyManager
from affinity_cli.core.wine_manager import WineManager
from affinity_cli.core.prefix_manager import PrefixManager
from affinity_cli.core.affinity_installer import AffinityInstaller

console = Console()


def run_report(output_path: Optional[str] = None, verbose: bool = False):
    """
    Generate system report
    
    Args:
        output_path: Path to save report (None = print to console)
        verbose: Include detailed information
    """
    console.print(Panel.fit(
        "[bold cyan]Affinity CLI - System Report[/bold cyan]",
        border_style="cyan"
    ))
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "affinity_cli_version": __version__,
        "system": {},
        "dependencies": {},
        "wine": {},
        "prefix": {},
        "products": {},
    }
    
    # System Information
    console.print("\n[bold]Gathering System Information...[/bold]")
    detector = DistroDetector()
    report["system"] = detector.get_distro_info()
    
    # Dependencies
    console.print("[bold]Checking Dependencies...[/bold]")
    dep_manager = DependencyManager(detector)
    missing = dep_manager.get_missing_dependencies()
    
    report["dependencies"] = {
        "critical_met": dep_manager.verify_dependencies(),
        "missing_count": len(missing),
        "missing_packages": missing[:20] if verbose else missing[:5],
    }
    
    # Wine
    console.print("[bold]Checking Wine...[/bold]")
    wine_manager = WineManager()
    
    report["wine"] = {
        "installed": wine_manager.check_wine_installed(),
        "path": str(wine_manager.wine_path) if wine_manager.wine_path else None,
        "version": wine_manager.get_wine_version(),
    }
    
    # Prefix
    console.print("[bold]Checking Wine Prefix...[/bold]")
    try:
        prefix_manager = PrefixManager()
        report["prefix"] = {
            "exists": prefix_manager.prefix_exists(),
            "path": str(prefix_manager.prefix_path),
        }
    except RuntimeError:
        report["prefix"] = {
            "exists": False,
            "path": str(config.DEFAULT_WINE_PREFIX),
            "error": "Wine not available"
        }
    
    # Installed Products
    console.print("[bold]Checking Installed Products...[/bold]")
    try:
        affinity_installer = AffinityInstaller()
        installed = affinity_installer.list_installed_products()
        
        products_info = {}
        for product in installed:
            product_path = affinity_installer.get_product_path(product)
            products_info[product] = {
                "name": config.AFFINITY_PRODUCTS[product]["name"],
                "installed": True,
                "path": str(product_path) if product_path else None,
            }
        
        report["products"] = products_info
    except RuntimeError:
        report["products"] = {"error": "Cannot check (Wine not available)"}
    
    # Output report
    if output_path:
        output_file = Path(output_path)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        console.print(f"\n✓ Report saved to: {output_file}")
    else:
        console.print("\n[bold]Report Summary:[/bold]")
        console.print(json.dumps(report, indent=2))
    
    console.print()
