"""
Uninstall Command
Remove Affinity products and optionally Wine/prefix
"""

from typing import List
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
import shutil

from affinity_cli import config
from affinity_cli.core.wine_manager import WineManager
from affinity_cli.core.affinity_installer import AffinityInstaller
from affinity_cli.core.desktop_integration import DesktopIntegration

console = Console()


def run_uninstall(products: List[str], purge: bool = False, verbose: bool = False):
    """
    Uninstall Affinity products
    
    Args:
        products: List of products to uninstall (empty = all)
        purge: Remove everything including Wine prefix
        verbose: Verbose output
    """
    console.print(Panel.fit(
        "[bold yellow]Affinity CLI - Uninstaller[/bold yellow]\n"
        "This will remove Affinity products from your system",
        border_style="yellow"
    ))
    
    try:
        # Get installed products
        try:
            affinity_installer = AffinityInstaller()
            installed = affinity_installer.list_installed_products()
        except RuntimeError:
            console.print("\n[red]Wine not found. Cannot proceed with uninstall.[/red]")
            return
        
        if not installed:
            console.print("\n[yellow]No Affinity products are installed[/yellow]")
            return
        
        # Determine what to uninstall
        if products:
            to_uninstall = [p for p in products if p in installed]
            if not to_uninstall:
                console.print(f"\n[yellow]None of the specified products are installed[/yellow]")
                return
        else:
            to_uninstall = installed
        
        # Confirm uninstallation
        console.print("\n[bold]Products to uninstall:[/bold]")
        for product in to_uninstall:
            product_name = config.AFFINITY_PRODUCTS[product]['name']
            console.print(f"  • {product_name}")
        
        if purge:
            console.print("\n[bold red]⚠ Purge mode enabled:[/bold red]")
            console.print("  • Wine prefix will be removed")
            console.print("  • All Affinity data will be lost")
        
        if not Confirm.ask("\nProceed with uninstallation?", default=False):
            console.print("[yellow]Uninstall cancelled[/yellow]")
            return
        
        # Uninstall products
        console.print("\n[bold]Uninstalling Products[/bold]")
        
        desktop_integration = DesktopIntegration()
        
        for product in to_uninstall:
            product_name = config.AFFINITY_PRODUCTS[product]['name']
            console.print(f"\n  • Uninstalling {product_name}...")
            
            # Remove desktop integration
            success, msg = desktop_integration.remove_integration(product)
            if success:
                console.print(f"    ✓ Desktop integration removed")
            
            # Uninstall product
            success, msg = affinity_installer.uninstall_product(product)
            if success:
                console.print(f"    ✓ {msg}")
            else:
                console.print(f"    [yellow]Warning: {msg}[/yellow]")
        
        # Purge if requested
        if purge:
            console.print("\n[bold]Purging Installation[/bold]")
            
            # Confirm again for purge
            if Confirm.ask("  Remove Wine prefix? (all data will be lost)", default=False):
                prefix_path = config.DEFAULT_WINE_PREFIX
                
                if prefix_path.exists():
                    try:
                        shutil.rmtree(prefix_path)
                        console.print(f"  ✓ Wine prefix removed: {prefix_path}")
                    except Exception as e:
                        console.print(f"  [red]✗ Failed to remove prefix: {e}[/red]")
            
            # Remove Wine installation
            if Confirm.ask("  Remove Wine installation?", default=False):
                wine_manager = WineManager()
                wine_dir = wine_manager.wine_dir
                
                if wine_dir.exists():
                    try:
                        shutil.rmtree(wine_dir)
                        console.print(f"  ✓ Wine removed: {wine_dir}")
                    except Exception as e:
                        console.print(f"  [red]✗ Failed to remove Wine: {e}[/red]")
            
            # Clean cache
            if config.CACHE_DIR.exists():
                try:
                    shutil.rmtree(config.CACHE_DIR)
                    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    console.print(f"  ✓ Cache cleaned")
                except Exception as e:
                    console.print(f"  [yellow]Warning: Failed to clean cache: {e}[/yellow]")
        
        # Success message
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            "[bold green]✓ Uninstall Complete[/bold green]\n\n"
            f"Removed: {', '.join([config.AFFINITY_PRODUCTS[p]['name'] for p in to_uninstall])}\n\n"
            "[dim]Thank you for trying Affinity CLI[/dim]",
            border_style="green"
        ))
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Uninstall cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Uninstall failed: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
