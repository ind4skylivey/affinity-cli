#!/usr/bin/env python3
"""Command-line entrypoint for Affinity CLI."""

from __future__ import annotations

import sys
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel

from affinity_cli import __version__, config
from affinity_cli.core.config_loader import ConfigError, ConfigLoader


@click.group()
@click.version_option(version=__version__, prog_name="affinity-cli")
@click.option(
    "--config",
    "config_file",
    type=click.Path(dir_okay=False, resolve_path=True),
    help="Path to a custom affinity-cli config file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose status output")
@click.pass_context
def cli(ctx: click.Context, config_file: Optional[str], verbose: bool) -> None:
    """Top-level CLI group used by every command."""

    try:
        loader = ConfigLoader(config_file)
    except ConfigError as exc:  # pragma: no cover - user error path
        raise click.ClickException(str(exc)) from exc

    ctx.ensure_object(dict)
    ctx.obj["config_loader"] = loader
    ctx.obj["verbose"] = verbose
    ctx.obj["console"] = Console()


@cli.command(name="list-installers")
@click.option("--path", "installers_path", type=click.Path(file_okay=False), help="Directory to scan")
@click.option(
    "--version",
    "version_filter",
    type=click.Choice(config.SUPPORTED_INSTALLER_VERSIONS),
    help="Filter by installer train",
)
@click.pass_context
def list_installers_cmd(
    ctx: click.Context,
    installers_path: Optional[str],
    version_filter: Optional[str],
) -> None:
    """List every installer detected in the configured directory."""

    loader: ConfigLoader = ctx.obj["config_loader"]
    settings = loader.derive(installers_path=installers_path)

    from affinity_cli.commands.list_installers import run_list_installers

    run_list_installers(settings=settings, version_filter=version_filter, console=ctx.obj["console"])


@cli.command(name="install")
@click.argument("target", type=click.Choice(["photo", "designer", "publisher", "all"], case_sensitive=False))
@click.option(
    "--version",
    "version_choice",
    type=click.Choice(config.SUPPORTED_INSTALLER_VERSIONS),
    help="Installer train to install (overrides config)",
)
@click.option("--prefix", "prefix_path", type=click.Path(file_okay=False), help="Wine prefix override")
@click.option("--installers", "installers_path", type=click.Path(file_okay=False), help="Installer directory override")
@click.option("--silent", is_flag=True, help="Skip confirmation prompts")
@click.option("--dry-run", is_flag=True, help="Log actions without executing installers")
@click.pass_context
def install_cmd(
    ctx: click.Context,
    target: str,
    version_choice: Optional[str],
    prefix_path: Optional[str],
    installers_path: Optional[str],
    silent: bool,
    dry_run: bool,
) -> None:
    """Install Affinity Photo, Designer, Publisher, or all of them."""

    loader: ConfigLoader = ctx.obj["config_loader"]
    settings = loader.derive(
        installers_path=installers_path,
        prefix_path=prefix_path,
        version=version_choice,
    )

    if target.lower() == "all":
        product_targets: List[str] = list(config.AFFINITY_PRODUCTS.keys())
    else:
        product_targets = [target.lower()]

    from affinity_cli.commands.install import run_install

    run_install(
        product_targets=product_targets,
        settings=settings,
        console=ctx.obj["console"],
        silent=silent,
        dry_run=dry_run,
    )


@cli.command(name="status")
@click.option("--prefix", "prefix_path", type=click.Path(file_okay=False), help="Inspect a specific Wine prefix")
@click.option("--installers", "installers_path", type=click.Path(file_okay=False), help="Override installer directory")
@click.pass_context
def status_cmd(
    ctx: click.Context,
    prefix_path: Optional[str],
    installers_path: Optional[str],
) -> None:
    """Display environment readiness, installer availability, and installed products."""

    loader: ConfigLoader = ctx.obj["config_loader"]
    settings = loader.derive(installers_path=installers_path, prefix_path=prefix_path)

    from affinity_cli.commands.status import run_status

    run_status(settings=settings, console=ctx.obj["console"], verbose=ctx.obj["verbose"])


def main() -> None:
    """Execute the CLI and present friendly error messages."""

    try:
        cli(obj={})
    except click.ClickException as exc:
        Console().print(Panel.fit(str(exc), border_style="red"))
        sys.exit(1)
    except KeyboardInterrupt:
        Console().print("[yellow]\nOperation cancelled by user[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
