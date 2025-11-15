"""CLI entry point for affinity-cli."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, cast

import click
from rich.console import Console
from rich.table import Table

from affinity_cli import __version__
from affinity_cli.config import ConfigLoader, UserConfig
from affinity_cli.installer_discovery import (
    InstallerDiscovery,
    InstallerInfo,
    PRODUCT_NAMES,
    VersionLiteral,
)
from affinity_cli.wine import WineExecutor

console = Console()


def _resolve_config(
    loader: ConfigLoader,
    installers_path: Optional[str],
    wine_prefix: Optional[str],
    default_version: Optional[str],
) -> UserConfig:
    config = loader.load()
    overrides = {}
    if installers_path:
        overrides["installers_path"] = Path(installers_path)
    if wine_prefix:
        overrides["wine_prefix"] = Path(wine_prefix)
    if default_version:
        overrides["default_version"] = default_version.lower()
    if overrides:
        config = config.with_overrides(**overrides)
    config.validate()
    return config


@click.group()
@click.version_option(version=__version__, prog_name="affinity-cli")
@click.option(
    "--config",
    "config_file",
    type=click.Path(path_type=Path),
    help="Path to a custom configuration file",
)
@click.pass_context
def cli(ctx: click.Context, config_file: Optional[Path]) -> None:
    """Install Affinity Photo, Designer, and Publisher with one command."""

    loader = ConfigLoader(config_file=config_file) if config_file else ConfigLoader()
    ctx.ensure_object(dict)
    ctx.obj["config_loader"] = loader


@cli.command("list-installers")
@click.option("--installers-path", type=click.Path(path_type=Path), help="Override installer path")
@click.pass_context
def list_installers(ctx: click.Context, installers_path: Optional[Path]) -> None:
    """List discovered installers."""

    config = _resolve_config(
        ctx.obj["config_loader"],
        installers_path=str(installers_path) if installers_path else None,
        wine_prefix=None,
        default_version=None,
    )
    discovery = InstallerDiscovery(config.installers_path)
    summary = discovery.summary()
    table = Table(title="Available installers", show_lines=True)
    table.add_column("Product")
    table.add_column("Version")
    table.add_column("File")
    any_found = False
    for product, entries in summary.items():
        if not entries:
            table.add_row(PRODUCT_NAMES[product], "-", "(not found)")
            continue
        any_found = True
        for installer in entries:
            table.add_row(
                PRODUCT_NAMES[product],
                f"{installer.version.upper()} ({installer.file_version})",
                installer.path.name,
            )
    console.print(table)
    if not any_found:
        console.print(
            f"[yellow]No installers detected in {config.installers_path}."
            " Place official Affinity installers inside this directory.[/yellow]"
        )


def _parse_targets(target: str) -> List[str]:
    if target == "all":
        return list(PRODUCT_NAMES.keys())
    return [target]


@cli.command("install")
@click.argument(
    "target",
    type=click.Choice(["photo", "designer", "publisher", "all"], case_sensitive=False),
)
@click.option("--version", "preferred_version", type=click.Choice(["v1", "v2"]))
@click.option("--installers-path", type=click.Path(path_type=Path))
@click.option("--prefix", "wine_prefix", type=click.Path(path_type=Path))
@click.option("--silent", is_flag=True, help="Attempt silent install")
@click.option("--dry-run", is_flag=True, help="Show actions without executing")
@click.pass_context
def install_command(
    ctx: click.Context,
    target: str,
    preferred_version: Optional[str],
    installers_path: Optional[Path],
    wine_prefix: Optional[Path],
    silent: bool,
    dry_run: bool,
) -> None:
    """Install one or more Affinity products."""

    config = _resolve_config(
        ctx.obj["config_loader"],
        installers_path=str(installers_path) if installers_path else None,
        wine_prefix=str(wine_prefix) if wine_prefix else None,
        default_version=preferred_version,
    )
    discovery = InstallerDiscovery(config.installers_path)
    executor = WineExecutor(config.wine_prefix)
    targets = _parse_targets(target)
    forced_version: Optional[VersionLiteral] = None
    if preferred_version:
        forced_version = cast(VersionLiteral, preferred_version)
    elif config.default_version == "v1":
        forced_version = "v1"

    for product in targets:
        try:
            installer = discovery.select_installer(product, forced_version)
        except FileNotFoundError as exc:
            raise click.ClickException(str(exc)) from exc
        _run_installer(product, installer, executor, silent=silent, dry_run=dry_run)


def _run_installer(
    product: str,
    installer: InstallerInfo,
    executor: WineExecutor,
    silent: bool,
    dry_run: bool,
) -> None:
    console.print(
        f"[green]Installing {PRODUCT_NAMES[product]} using {installer.path.name} ({installer.version.upper()}).[/green]"
    )
    executor.run_installer(installer.path, silent=silent, dry_run=dry_run)
    console.print(f"[bold green]Finished {PRODUCT_NAMES[product]} installation.[/bold green]")


@cli.command("status")
@click.option("--installers-path", type=click.Path(path_type=Path))
@click.option("--prefix", "wine_prefix", type=click.Path(path_type=Path))
@click.pass_context
def status(ctx: click.Context, installers_path: Optional[Path], wine_prefix: Optional[Path]) -> None:
    """Show configuration and discovery status."""

    config = _resolve_config(
        ctx.obj["config_loader"],
        installers_path=str(installers_path) if installers_path else None,
        wine_prefix=str(wine_prefix) if wine_prefix else None,
        default_version=None,
    )
    discovery = InstallerDiscovery(config.installers_path)
    console.print("[bold underline]Configuration[/bold underline]")
    console.print(f"Installers path: {config.installers_path} ({_exists_label(config.installers_path)})")
    console.print(f"Wine prefix: {config.wine_prefix} ({_exists_label(config.wine_prefix)})")
    console.print(f"Default version preference: {config.default_version.upper()}")
    console.print()
    table = Table(title="Installer inventory", show_lines=True)
    table.add_column("Product")
    table.add_column("Details")
    for product, entries in discovery.summary().items():
        if entries:
            summary = ", ".join(f"{inst.version.upper()}-{inst.file_version}" for inst in entries)
        else:
            summary = "missing"
        table.add_row(PRODUCT_NAMES[product], summary)
    console.print(table)


def _exists_label(path: Path) -> str:
    return "exists" if path.exists() else "missing"


def main() -> None:
    cli(obj={})


if __name__ == "__main__":  # pragma: no cover
    main()
