"""
Repair Command
Fix broken installations and configurations
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from affinity_cli import config
from affinity_cli.core.dependency_manager import DependencyManager
from affinity_cli.core.wine_manager import WineManager
from affinity_cli.core.prefix_manager import PrefixManager
from affinity_cli.core.affinity_installer import AffinityInstaller
from affinity_cli.core.desktop_integration import DesktopIntegration

console = Console()


def run_repair(product: Optional[str] = None, verbose: bool = False):
    """
    Repair broken installation
    
    Args:
        product: Specific product to repair (None = repair all)
        verbose: Verbose output
    """
    console.print(Panel.fit(
        "[bold cyan]Affinity CLI - Repair Tool[/bold cyan]\n"
        "This will attempt to fix common issues",
        border_style="cyan"
    ))
    
    try:
        # Step 1: Verify Dependencies
        console.print("\n[bold]Step 1: Checking Dependencies[/bold]")
        
        dep_manager = DependencyManager()
        
        if dep_manager.verify_dependencies():
            console.print("  ✓ All critical dependencies present")
        else:
            console.print("  [yellow]✗ Missing critical dependencies[/yellow]")
            missing = dep_manager.get_missing_dependencies()
            console.print(f"    Missing: {', '.join(missing[:5])}")
            console.print("    [dim]Run 'affinity-cli install' to install dependencies[/dim]")
        
        # Step 2: Check Wine
        console.print("\n[bold]Step 2: Checking Wine Installation[/bold]")
        
        wine_manager = WineManager()
        
        if wine_manager.check_wine_installed():
            console.print(f"  ✓ Wine found at {wine_manager.wine_bin}")
        else:
            console.print("  [yellow]✗ Wine not installed[/yellow]")
            console.print("    [dim]Run 'affinity-cli install' to install Wine[/dim]")
            return
        
        # Step 3: Check/Repair Wine Prefix
        console.print("\n[bold]Step 3: Checking Wine Prefix[/bold]")
        
        prefix_manager = PrefixManager(wine_manager=wine_manager)
        
        if prefix_manager.prefix_exists():
            console.print(f"  ✓ Prefix exists at {prefix_manager.prefix_path}")
            
            # Try to repair prefix
            console.print("  • Running wineboot --update...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Repairing prefix...", total=None)
                
                try:
                    import subprocess
                    import os
                    
                    env = os.environ.copy()
                    env["WINEPREFIX"] = str(prefix_manager.prefix_path)
                    env["WINEDEBUG"] = "-all"
                    
                    result = subprocess.run(
                        [str(wine_manager.wine_path), "wineboot", "--update"],
                        env=env,
                        capture_output=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        console.print("  ✓ Prefix repaired")
                    else:
                        console.print("  [yellow]⚠ Repair completed with warnings[/yellow]")
                
                except Exception as e:
                    console.print(f"  [yellow]⚠ Repair error: {e}[/yellow]")
        else:
            console.print(f"  [yellow]✗ Prefix does not exist[/yellow]")
            console.print("    [dim]Run 'affinity-cli install' to create prefix[/dim]")
            return
        
        # Step 4: Check Installed Products
        console.print("\n[bold]Step 4: Checking Installed Products[/bold]")
        
        affinity_installer = AffinityInstaller(wine_manager=wine_manager)
        installed = affinity_installer.list_installed_products()
        
        if not installed:
            console.print("  [yellow]No Affinity products installed[/yellow]")
            return
        
        # Determine products to repair
        if product:
            if product in installed:
                products_to_repair = [product]
            else:
                console.print(f"  [yellow]✗ {product} is not installed[/yellow]")
                return
        else:
            products_to_repair = installed
        
        console.print(f"  Found {len(installed)} installed product(s):")
        for p in installed:
            console.print(f"    • {config.AFFINITY_PRODUCTS[p]['name']}")
        
        # Step 5: Repair Desktop Integration
        console.print("\n[bold]Step 5: Repairing Desktop Integration[/bold]")
        
        desktop_integration = DesktopIntegration(wine_manager=wine_manager)
        
        for p in products_to_repair:
            product_name = config.AFFINITY_PRODUCTS[p]['name']
            console.print(f"\n  • Repairing {product_name}...")
            
            # Remove old integration
            desktop_integration.remove_integration(p)
            
            # Recreate integration
            success, msg = desktop_integration.integrate_product(p)
            
            if success:
                console.print(f"    ✓ Desktop integration repaired")
            else:
                console.print(f"    [yellow]⚠ {msg}[/yellow]")
        
        # Update desktop database
        desktop_integration.update_desktop_database()
        
        # Success
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            "[bold green]✓ Repair Complete[/bold green]\n\n"
            "Installation has been repaired.\n"
            "If issues persist, try:\n"
            "  • affinity-cli uninstall --purge\n"
            "  • affinity-cli install",
            border_style="green"
        ))
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Repair cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Repair failed: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
