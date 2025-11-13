#!/usr/bin/env python3
"""
Affinity CLI - Main Entry Point
Complete CLI tool for installing Affinity products on Linux
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel

from affinity_cli import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="affinity-cli")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """
    🎨 Affinity CLI - Professional Install Tool for Linux
    
    Install Affinity Photo, Designer, and Publisher on any Linux distribution
    with a single, powerful command.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--products", "-p", default="", help="Products to install (photo,designer,publisher)")
@click.option("--installer-path", "-i", type=click.Path(exists=True), help="Path to installer directory")
@click.option("--wine-version", "-w", default="latest", help="Wine version to use")
@click.option("--prefix", type=click.Path(), help="Custom Wine prefix path")
@click.option("--skip-dependencies", is_flag=True, help="Skip dependency installation")
@click.option("--skip-multiarch", is_flag=True, help="Skip multiarch setup")
@click.pass_context
def install(ctx, products, installer_path, wine_version, prefix, skip_dependencies, skip_multiarch):
    """Install Affinity products"""
    from affinity_cli.commands.install import run_install
    
    verbose = ctx.obj.get("verbose", False)
    
    run_install(
        products=products.split(",") if products else [],
        installer_path=installer_path,
        wine_version=wine_version,
        prefix_path=prefix,
        skip_dependencies=skip_dependencies,
        skip_multiarch=skip_multiarch,
        verbose=verbose
    )


@cli.command()
@click.pass_context
def status(ctx):
    """Check installation status and system information"""
    from affinity_cli.commands.status import run_status
    
    verbose = ctx.obj.get("verbose", False)
    run_status(verbose=verbose)


@cli.command()
@click.option("--product", "-p", help="Product to repair (photo, designer, publisher)")
@click.pass_context
def repair(ctx, product):
    """Repair broken installation"""
    from affinity_cli.commands.repair import run_repair
    
    verbose = ctx.obj.get("verbose", False)
    run_repair(product=product, verbose=verbose)


@cli.command()
@click.option("--products", "-p", help="Products to uninstall (comma-separated)")
@click.option("--purge", is_flag=True, help="Remove everything including Wine prefix")
@click.pass_context
def uninstall(ctx, products, purge):
    """Uninstall Affinity products"""
    from affinity_cli.commands.uninstall import run_uninstall
    
    verbose = ctx.obj.get("verbose", False)
    product_list = products.split(",") if products else []
    
    run_uninstall(products=product_list, purge=purge, verbose=verbose)


@cli.command()
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.pass_context
def report(ctx, output):
    """Generate system report"""
    from affinity_cli.commands.report import run_report
    
    verbose = ctx.obj.get("verbose", False)
    run_report(output_path=output, verbose=verbose)


@cli.command()
def welcome():
    """Show welcome message and project info"""
    welcome_text = f"""
[bold cyan]AFFINITY CLI - Linux Installation Toolkit[/bold cyan]

[yellow]Version:[/yellow] {__version__}
[yellow]Purpose:[/yellow] Universal Affinity product installation on Linux

[bold green]Quick Start:[/bold green]

1. [cyan]affinity-cli install[/cyan]
   Complete installation with all dependencies

2. [cyan]affinity-cli status[/cyan]
   Check current installation status

3. [cyan]affinity-cli uninstall[/cyan]
   Clean uninstall of products

[bold magenta]🔗 Community & Support:[/bold magenta]
GitHub: https://github.com/yourusername/affinity-cli
Docs: https://affinity-cli.readthedocs.io/

[dim]Use --help with any command for detailed options[/dim]
    """
    
    panel = Panel(
        welcome_text,
        title="[bold]Welcome to Affinity CLI[/bold]",
        expand=False,
        border_style="cyan"
    )
    console.print(panel)


def main():
    """Main entry point"""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[red]Operation cancelled by user[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]", style="bold")
        sys.exit(1)


if __name__ == "__main__":
    main()
