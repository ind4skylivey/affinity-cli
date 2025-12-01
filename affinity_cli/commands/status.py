"""Implementation of the `affinity-cli status` command."""

from __future__ import annotations

import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from affinity_cli import config
from affinity_cli.core.affinity_installer import AffinityInstaller
from affinity_cli.core.config_loader import ResolvedConfig
from affinity_cli.core.distro_detector import DistroDetector
from affinity_cli.core.installer_scanner import InstallerScanner


def run_status(*, settings: ResolvedConfig, console: Console, verbose: bool) -> None:
    """Display a holistic view of the current installation state."""

    console.print(Panel.fit("Affinity CLI Status", border_style="cyan"))

    _render_config(settings, console)
    _render_distro(console)
    _render_installers(settings, console)
    _render_wine(settings, console)
    _render_products(settings, console, verbose)


def _render_config(settings: ResolvedConfig, console: Console) -> None:
    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in settings.to_display_dict().items():
        table.add_row(key, value)

    console.print(table)


def _render_distro(console: Console) -> None:
    detector = DistroDetector()
    distro_info = detector.get_distro_info()

    table = Table(title="Detected distribution")
    table.add_column("Attribute", style="cyan")
    table.add_column("Value")

    for key in ["name", "version", "family", "package_manager"]:
        table.add_row(key.capitalize(), str(distro_info.get(key, "unknown")))

    console.print(table)


def _render_installers(settings: ResolvedConfig, console: Console) -> None:
    scanner = InstallerScanner(settings.installers_path, config.CACHE_DIR)
    candidates = scanner.scan()

    if not candidates:
        console.print(
            Panel.fit(
                "Universal installer not found locally. It will be downloaded automatically when needed.",
                border_style="yellow",
            )
        )
        return

    latest = candidates[0]
    console.print(
        Panel.fit(
            "\n".join(
                [
                    "Affinity Universal installer is available.",
                    f"Path: {latest.path}",
                    f"Size: {latest.human_size}",
                ]
            ),
            border_style="green",
        )
    )


def _render_wine(settings: ResolvedConfig, console: Console) -> None:
    prefix = settings.wine_prefix
    drive_c = prefix / "drive_c"
    prefix_exists = drive_c.exists()

    wine_path = shutil.which("wine64") or shutil.which("wine")
    wine_status = wine_path if wine_path else "Not found in PATH"

    table = Table(title="Wine environment")
    table.add_column("Item", style="cyan")
    table.add_column("Value")
    table.add_row("Wine binary", wine_status)
    table.add_row("Prefix", str(prefix))
    table.add_row("Prefix ready", "yes" if prefix_exists else "no")

    console.print(table)


def _render_products(settings: ResolvedConfig, console: Console, verbose: bool) -> None:
    try:
        installer = AffinityInstaller(prefix_path=settings.wine_prefix)
    except RuntimeError as exc:
        console.print(Panel.fit(f"Unable to inspect products: {exc}", border_style="red"))
        return

    installed = installer.list_installed_products()

    if not installed:
        console.print(
            Panel.fit(
                "No Affinity applications detected in the configured prefix.",
                border_style="yellow",
            )
        )
        return

    table = Table(title="Installed products")
    table.add_column("Product", style="cyan")
    table.add_column("Executable")

    for product in installed:
        path = installer.get_product_path(product)
        entry = str(path) if (path and verbose) else config.AFFINITY_PRODUCTS[product]["name"]
        table.add_row(config.AFFINITY_PRODUCTS[product]["name"], entry)

    console.print(table)
