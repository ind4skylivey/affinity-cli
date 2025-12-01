"""Implementation of the `affinity-cli list-installers` command."""

from __future__ import annotations

from typing import Iterable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from affinity_cli import config
from affinity_cli.core.installer_scanner import InstallerScanner
from affinity_cli.core.config_loader import ResolvedConfig


def run_list_installers(
    *,
    settings: ResolvedConfig,
    version_filter: Optional[str],
    console: Console,
) -> None:
    """Display all installers discovered in the configured path."""

    root = settings.installers_path
    console.print(Panel.fit(f"Scanning {root}", border_style="cyan"))

    if not root.exists():
        console.print(
            Panel.fit(
                "Installer path does not exist. Download the Affinity installers from Serif "
                "and place them inside the configured directory.",
                border_style="red",
            )
        )
        return

    scanner = InstallerScanner(root, config.CACHE_DIR)
    candidates = scanner.scan()

    if not candidates:
        console.print(
            Panel.fit(
                "No universal installer found. It will be downloaded automatically during `affinity-cli install`.",
                border_style="yellow",
            )
        )
        return

    table = Table(title="Discovered installers")
    table.add_column("Installer", style="cyan")
    table.add_column("Version", justify="center")
    table.add_column("Size")
    table.add_column("Location", overflow="fold")

    for candidate in candidates:
        table.add_row(
            "Affinity Universal",
            candidate.version_label,
            candidate.human_size,
            str(candidate.path),
        )

    console.print(table)

    console.print(
        Panel.fit(
            f"{len(candidates)} installer(s) available across {len({c.source for c in candidates})} location(s).",
            border_style="green",
        )
    )


def _count_by_version(candidates: Iterable) -> dict:
    # kept for backward compatibility with tests; universal is the only valid version now.
    summary = {"universal": len(list(candidates))}
    return summary
