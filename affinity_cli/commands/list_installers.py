"""Implementation of the `affinity-cli list-installers` command."""

from __future__ import annotations

from typing import Iterable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from affinity_cli import config
from affinity_cli.core.installer_scanner import InstallerScanner


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

    scanner = InstallerScanner(root)
    candidates = scanner.scan()

    if version_filter:
        candidates = [c for c in candidates if c.version_type == version_filter]

    if not candidates:
        console.print(
            Panel.fit(
                "No installers found. Supported files must start with 'Affinity' and end in .exe or .msi.",
                border_style="yellow",
            )
        )
        return

    table = Table(title="Discovered installers")
    table.add_column("Product", style="cyan")
    table.add_column("Version train", style="magenta")
    table.add_column("Version", justify="center")
    table.add_column("File", overflow="fold")

    for candidate in candidates:
        table.add_row(
            config.AFFINITY_PRODUCTS[candidate.product]["name"],
            candidate.version_type,
            candidate.version_label,
            str(candidate.path),
        )

    console.print(table)

    counts = _count_by_version(candidates)
    summary_lines = [f"{version}: {count}" for version, count in counts.items()]
    console.print(
        Panel.fit(
            "Installer summary:\n" + "\n".join(summary_lines),
            border_style="green",
        )
    )


def _count_by_version(candidates: Iterable) -> dict:
    summary = {"v1": 0, "v2": 0}
    for candidate in candidates:
        summary[candidate.version_type] = summary.get(candidate.version_type, 0) + 1
    return summary
