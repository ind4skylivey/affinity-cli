"""Prefix preparation for running the Affinity Universal installer under Wine."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from affinity_cli.utils.logger import logger


class PrefixPrepareError(RuntimeError):
    """Raised when the Wine prefix cannot be prepared for installation."""


@dataclass
class PrefixPreparer:
    prefix_path: Path
    wine_binary: Path
    env: Dict[str, str]
    marker_name: str = ".affinity_cli_prepared"
    profile: str = "standard"

    PROFILE_COMPONENTS = {
        "minimal": [
            "win11",
            "corefonts",
            "tahoma",
            "crypt32",
            "d3dcompiler_47",
        ],
        "standard": [
            "win11",
            "corefonts",
            "tahoma",
            "crypt32",
            "d3dcompiler_47",
            "vcrun2022",
        ],
        "full": [
            "win11",
            "corefonts",
            "tahoma",
            "crypt32",
            "d3dcompiler_47",
            "vcrun2022",
            "dotnet48",
            "dxvk",
            "vkd3d",
            "remove_mono",
        ],
    }
    PROFILE_ORDER = ["minimal", "standard", "full"]

    def prepare(self, console) -> None:
        """Prepare the prefix to match the AffinityOnLinux Wine guide."""
        marker = self.prefix_path / self.marker_name
        previous_profile = marker.read_text(encoding="utf-8").strip() if marker.exists() else None

        profile = self.profile or "standard"

        if profile not in self.PROFILE_COMPONENTS:
            console.print("[bold red]Error: invalid or missing Wine profile.[/bold red]")
            console.print("Valid options are: minimal, standard, full.")
            console.print("You can also force one with: AFFINITY_WINE_PROFILE=standard affinity-cli install")
            raise SystemExit(1)

        target_components = self.PROFILE_COMPONENTS[profile]
        previous_components: List[str] = self.PROFILE_COMPONENTS.get(previous_profile, []) if previous_profile else []
        missing_components = [c for c in target_components if c not in previous_components]

        if previous_profile == self.profile and not missing_components:
            logger.info("Prefix already prepared with profile '%s' (marker found at %s)", self.profile, marker)
            return

        console.print("[cyan]Preparing Wine prefix for Affinity (win11, DXVK/vkd3d, core runtimes)...[/cyan]")
        self._set_windows_version("win11")
        if missing_components:
            note = ""
            if self.profile == "full":
                note = " (this may take several minutes: dotnet48 + DXVK/VKD3D)"
            console.print(
                f"[cyan]Wine profile: {self.profile}[/cyan] {note}\n"
                f"Installing Wine components: {', '.join(missing_components)}"
            )
            self._install_winetricks_components(missing_components, console)
        else:
            console.print(f"[green]No additional components needed for profile '{self.profile}'.[/green]")
        self._set_windows_version_registry("win11")
        self._touch_marker(marker, self.profile)
        console.print("[green]Prefix preparation complete.[/green]")

    # ---------------- internal helpers ---------------- #
    def _set_windows_version(self, version: str) -> None:
        # Non-interactive Windows version set (idempotent).
        cmd = [str(self.wine_binary), "winecfg", "/v", version]
        try:
            self._run(cmd, f"Setting Windows version to {version}")
        except PrefixPrepareError as exc:
            raise PrefixPrepareError(
                f"Failed to set Windows version to {version}. "
                "Try running 'winecfg -v win10' manually inside your environment. "
                f"Details: {exc}"
            ) from exc

    def _set_windows_version_registry(self, version: str) -> None:
        """Force Windows version via registry for HKCU and HKLM."""
        current_version = "10.0" if version.lower().startswith("win10") else "11.0"
        product_name = "Windows 10 Pro" if current_version.startswith("10") else "Windows 11 Pro"
        reg_content = f"""
REGEDIT4

[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows NT\\CurrentVersion]
"CurrentVersion"="{current_version}"
"CurrentBuildNumber"="19045"
"CurrentBuild"="19045"
"ProductName"="{product_name}"

[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion]
"CurrentVersion"="{current_version}"
"CurrentBuildNumber"="19045"
"CurrentBuild"="19045"
"ProductName"="{product_name}"
"""
        reg_path = self.prefix_path / "drive_c" / "set_winver.reg"
        try:
            reg_path.write_text(reg_content, encoding="utf-8")
        except OSError as exc:
            raise PrefixPrepareError(f"Failed to write registry file: {exc}") from exc

        cmd = [str(self.wine_binary), "regedit", "/S", str(reg_path)]
        try:
            self._run(cmd, "Applying Windows version registry keys")
        finally:
            try:
                reg_path.unlink(missing_ok=True)
            except OSError:
                pass

    def verify_windows_version(self) -> bool:
        """Check if registry reports Windows 10/11. Non-blocking if inconclusive."""
        cmd = [str(self.wine_binary), "reg", "query", r"HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion", "/v", "CurrentVersion"]
        try:
            result = subprocess.run(
                cmd,
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as exc:
            raise PrefixPrepareError(f"Failed to query Windows version: {exc}") from exc

        output = (result.stdout or "") + (result.stderr or "")
        if "10." in output or "11." in output:
            logger.info("Confirmed Windows version via registry: %s", output.strip())
            return True

        logger.warning(
            "Warning: could not confirm prefix Windows version as 10/11; continuing. "
            "If the Affinity installer complains about Windows version, try reinstalling the prefix."
        )
        return False

    def _install_winetricks_components(self, components: List[str], console) -> None:
        winetricks = shutil.which("winetricks")
        if not winetricks:
            raise PrefixPrepareError(
                "winetricks is required to prepare the prefix (missing). "
                "Install winetricks (e.g., Ubuntu: sudo apt install winetricks; Arch/CachyOS: sudo pacman -S winetricks) and re-run."
            )
        cmd = [winetricks, "-q"] + components
        try:
            logger.info("Installing winetricks components: %s", ", ".join(components))
            process = subprocess.Popen(
                cmd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert process.stdout
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    console.print(f"[dim]{line}[/dim]")
                else:
                    console.print("[dim]winetricks is still running... please wait[/dim]")
            ret = process.wait()
            if ret != 0:
                raise PrefixPrepareError(
                    f"winetricks failed with exit code {ret}. Please retry or install components manually."
                )
        except OSError as exc:
            raise PrefixPrepareError(f"Failed to run winetricks: {exc}") from exc

    def _touch_marker(self, marker: Path, profile: str) -> None:
        try:
            marker.write_text(profile, encoding="utf-8")
        except OSError as exc:
            logger.debug("Could not write marker file: %s", exc)

    def _run(self, command: List[str], label: str) -> None:
        try:
            logger.info("%s: %s", label, " ".join(command))
            subprocess.run(
                command,
                env=self.env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise PrefixPrepareError(
                f"{label} failed with exit {exc.returncode}. Stderr:\n{exc.stderr.strip()}"
            ) from exc


__all__ = ["PrefixPreparer", "PrefixPrepareError"]
