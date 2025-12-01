"""Implementation of the `affinity-cli install` command."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from affinity_cli import config
from affinity_cli.core.affinity_installer import AffinityInstaller
from affinity_cli.core.config_loader import ResolvedConfig
from affinity_cli.core.downloader import DownloadError, SmartDownloader
from affinity_cli.core.distro_detector import DistroDetector
from affinity_cli.core.installer_scanner import InstallerCandidate, InstallerScanner
from affinity_cli.core.prefix_preparer import PrefixPreparer, PrefixPrepareError
from affinity_cli.core.preflight import PreflightChecker
from affinity_cli.core.wine_executor import WineExecutor, WineExecutorError


def run_install(
    *,
    settings: ResolvedConfig,
    console: Console,
    silent: bool,
    dry_run: bool,
    preflight_only: bool,
    wine_profile: str,
    download_url_override: Optional[str],
) -> None:
    """Install one or more Affinity products."""

    console.print(
        Panel.fit(
            "[bold cyan]Preparing installation[/bold cyan]",
            title="Affinity CLI",
            border_style="cyan",
        )
    )
    distro = DistroDetector().get_distro_info()
    console.print(
        f"[dim]Detected {distro.get('name', 'Linux')} {distro.get('version', '')} • auto-selecting available Wine/Proton from PATH[/dim]"
    )

    preflight_report = PreflightChecker().run()
    if preflight_report.issues:
        _render_preflight(preflight_report, console, silent)
    if not preflight_report.ok:
        console.print(
            Panel.fit(
                "Pre-flight checks failed. Resolve the above issues and re-run `affinity-cli install`.\n"
                "Hint: Install Wine/Proton and Vulkan drivers, then try again.",
                border_style="red",
            )
        )
        return

    if preflight_only:
        console.print(Panel.fit("Pre-flight checks passed. No actions executed (--preflight-only).", border_style="green"))
        return

    installer_path = _resolve_installer(settings, console, download_url_override)
    if not installer_path:
        return

    _render_install_plan(installer_path, console)

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

    try:
        preparer = PrefixPreparer(
            prefix_path=settings.wine_prefix,
            wine_binary=executor.wine_binary,
            env=executor._build_env(),
            profile=wine_profile,
        )
        preparer.prepare(console)
        if not preparer.verify_windows_version():
            raise PrefixPrepareError(
                "Prefix Windows version could not be confirmed as 10/11. Please rerun with a clean prefix."
            )
    except PrefixPrepareError as exc:
        console.print(
            Panel.fit(
                f"Prefix preparation failed:\n{exc}\n\n"
                "Install winetricks and ensure Vulkan/DXVK prerequisites are present, then retry.",
                border_style="red",
            )
        )
        return

    console.print(f"\n[bold]Installing Affinity Universal[/bold]\n{installer_path}")
    results = []
    try:
        result = executor.run_installer(installer_path, version_type="universal")
        if result.returncode != 0:
            raise WineExecutorError(
                f"Installer exited with code {result.returncode}.\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
            )
        results.append(("universal", True, "Installer completed"))
    except WineExecutorError as exc:
        results.append(("universal", False, str(exc)))

    effective_products = list(config.AFFINITY_PRODUCTS.keys())
    _post_install_summary(results, effective_products, settings, console, dry_run)


def _render_install_plan(
    installer_path: Path,
    console: Console,
) -> None:
    table = Table(title="Install plan (Universal)")
    table.add_column("Installer", style="cyan")
    table.add_column("File", overflow="fold")
    table.add_column("Size")

    candidate = InstallerCandidate(
        path=installer_path,
        version_label="universal",
        size_bytes=installer_path.stat().st_size if installer_path.exists() else 0,
        source=installer_path.parent,
    )
    table.add_row("Affinity Universal", str(candidate.path), candidate.human_size)

    console.print(table)


def _post_install_summary(
    results: List[tuple],
    product_targets: List[str],
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
        for product in product_targets:
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
        failure_lines = [message for _, _, message in failures]
        console.print(
            Panel.fit(
                "Installation issues encountered:\n" + "\n".join(failure_lines),
                border_style="red",
            )
        )


def _resolve_installer(settings: ResolvedConfig, console: Console, download_url_override: Optional[str]) -> Optional[Path]:
    scanner = InstallerScanner(settings.installers_path, config.CACHE_DIR)
    candidate = scanner.first()
    if candidate:
        console.print(f"[green]Found local installer at {candidate.path}[/green]")
        return candidate.path

    console.print(
        Panel.fit(
            "No local Affinity Universal installer detected. Attempting smart download...",
            border_style="yellow",
        )
    )
    downloader = SmartDownloader(console=console)
    try:
        return downloader.ensure_universal(
            download_url=download_url_override,
            configured_url=settings.download_url,
        )
    except DownloadError as exc:
        console.print(
            Panel.fit(
                f"Download failed: {exc}",
                border_style="red",
            )
        )
        return None


def _render_preflight(report, console: Console, silent: bool) -> None:
    if not report.issues:
        return
    err_lines = []
    warn_lines = []
    for issue in report.errors:
        line = f"[red]✗ {issue.message}[/red]"
        if issue.hint:
            line += f"\n    [dim]{issue.hint}[/dim]"
        err_lines.append(line)
    for issue in report.warnings:
        line = f"[yellow]! {issue.message}[/yellow]"
        if issue.hint:
            line += f"\n    [dim]{issue.hint}[/dim]"
        warn_lines.append(line)

    text = "\n".join(err_lines + warn_lines)
    console.print(
        Panel.fit(
            text or "Pre-flight checks completed.",
            title="Pre-flight",
            border_style="red" if report.errors else "yellow",
        )
    )
