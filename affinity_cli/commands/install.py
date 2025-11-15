"""Implementation of the `affinity-cli install` command."""

from __future__ import annotations

from typing import Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from affinity_cli import config
from affinity_cli.core.affinity_installer import AffinityInstaller
from affinity_cli.core.config_loader import ResolvedConfig
from affinity_cli.core.installer_scanner import InstallerCandidate, InstallerScanner
from affinity_cli.core.wine_executor import WineExecutor, WineExecutorError


def run_install(
    *,
    product_targets: List[str],
    settings: ResolvedConfig,
    console: Console,
    silent: bool,
    dry_run: bool,
) -> None:
    """Install one or more Affinity products."""

    console.print(
        Panel.fit(
            "[bold cyan]Preparing installation[/bold cyan]",
            title="Affinity CLI",
            border_style="cyan",
        )
    )

    scanner = InstallerScanner(settings.installers_path)
    selection: Dict[str, InstallerCandidate] = scanner.select(product_targets, settings.default_version)
    missing = [product for product in product_targets if product not in selection]

    if missing:
        console.print(
            f"[yellow]Missing installers for:[/yellow] {', '.join(missing)}\n"
            f"Looked in [bold]{settings.installers_path}[/bold] for {settings.default_version} builds."
        )

    if not selection:
        console.print(
            Panel.fit(
                "No installers available. Place Affinity setup files in the configured directory \n"
                "and run `affinity-cli list-installers` for verification.",
                title="No installers detected",
                border_style="red",
            )
        )
        return

    _render_install_plan(selection, console, settings.default_version)

    if dry_run:
        console.print(
            Panel.fit(
                "Dry-run mode enabled. Commands will not be executed.",
                border_style="blue",
            )
        )
    elif not silent:
        if not Confirm.ask("Continue with installation?", default=True):
            console.print("[yellow]Installation cancelled by user.[/yellow]")
            return

    executor = WineExecutor(
        settings.wine_prefix,
        dry_run=dry_run,
        silent=silent,
    )

    try:
        executor.ensure_prefix()
    except WineExecutorError as exc:
        console.print(f"[red]Wine prefix error:[/red] {exc}")
        return

    results = []
    for product in product_targets:
        candidate = selection.get(product)
        if not candidate:
            continue
        console.print(
            f"\n[bold]Installing {config.AFFINITY_PRODUCTS[product]['name']}[/bold]"
        )
        try:
            executor.run_installer(candidate.path, candidate.version_type)
            results.append((product, True, "Installer completed"))
        except WineExecutorError as exc:
            results.append((product, False, str(exc)))

    _post_install_summary(results, settings, console, dry_run)


def _render_install_plan(
    selection: Dict[str, InstallerCandidate],
    console: Console,
    installer_version: str,
) -> None:
    table = Table(title=f"Install plan ({installer_version})")
    table.add_column("Product", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("File", overflow="fold")
    table.add_column("Size")

    for product, candidate in selection.items():
        table.add_row(
            config.AFFINITY_PRODUCTS[product]["name"],
            candidate.version_label,
            str(candidate.path),
            candidate.human_size,
        )

    console.print(table)


def _post_install_summary(
    results: List[tuple],
    settings: ResolvedConfig,
    console: Console,
    dry_run: bool,
) -> None:
    successes = [item for item in results if item[1]]
    failures = [item for item in results if not item[1]]

    if dry_run:
        console.print(
            Panel.fit(
                "Dry-run completed. No changes were made.",
                border_style="cyan",
            )
        )
        return

    if successes:
        installer = AffinityInstaller(prefix_path=settings.wine_prefix)
        verified = []
        for product, *_ in successes:
            if installer.verify_installation(product):
                verified.append(config.AFFINITY_PRODUCTS[product]["name"])
        if verified:
            console.print(
                Panel.fit(
                    "\n".join(
                        [
                            "[green]Installation complete![/green]",
                            f"Verified: {', '.join(verified)}",
                            f"Wine prefix: {settings.wine_prefix}",
                        ]
                    ),
                    border_style="green",
                )
            )

    if failures:
        failure_lines = [
            f"{config.AFFINITY_PRODUCTS[product]['name']}: {message}"
            for product, _, message in failures
        ]
        console.print(
            Panel.fit(
                "Installation issues encountered:\n" + "\n".join(failure_lines),
                border_style="red",
            )
        )
