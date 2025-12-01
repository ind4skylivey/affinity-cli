"""High level helper for running installers under Wine."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from affinity_cli.utils.logger import logger


class WineExecutorError(RuntimeError):
    """Raised when Wine execution cannot continue."""


@dataclass
class CommandResult:
    command: Sequence[str]
    returncode: int
    stdout: str
    stderr: str


class WineExecutor:
    """Run commands inside a dedicated Wine prefix."""

    def __init__(
        self,
        prefix_path: Path,
        *,
        dry_run: bool = False,
        silent: bool = False,
        timeout_seconds: int = 1800,
    ) -> None:
        self.prefix_path = Path(prefix_path).expanduser()
        self.dry_run = dry_run
        self.silent = silent
        self.timeout_seconds = timeout_seconds
        self.wine_binary = self._resolve_wine_binary()

    def ensure_prefix(self) -> CommandResult:
        drive_c = self.prefix_path / "drive_c"
        if drive_c.exists():
            return CommandResult(["wineboot", "--init"], 0, "existing", "")
        if self.dry_run:
            message = f"dry-run: would initialize prefix at {self.prefix_path}"
            logger.info(message)
            return CommandResult(["wineboot", "--init"], 0, message, "")
        self.prefix_path.mkdir(parents=True, exist_ok=True)
        env = self._build_env()
        self._run_command([self._support_binary("wineboot"), "--init"], env=env, capture=True)
        self._run_command([self._support_binary("wineserver"), "-w"], env=env, capture=False, check=False)
        return CommandResult(["wineboot", "--init"], 0, "initialized", "")

    def run_installer(self, installer_path: Path, version_type: str) -> CommandResult:
        if not installer_path.exists():
            raise WineExecutorError(f"Installer not found: {installer_path}")
        env = self._build_env()
        arguments = self._installer_arguments(installer_path, version_type)
        command = [str(self.wine_binary)] + arguments
        return self._run_command(command, env=env, capture=True)

    def _installer_arguments(self, installer_path: Path, version_type: str) -> List[str]:
        # Default: launch the EXE directly (GUI). Keep optional quiet flags for legacy v1/v2.
        if version_type == "v2":
            return [str(installer_path), "/quiet", "/norestart"]
        return [str(installer_path)]

    def _run_command(
        self,
        command: Sequence[str],
        *,
        env: Optional[Dict[str, str]] = None,
        capture: bool = True,
        check: bool = True,
    ) -> CommandResult:
        if self.dry_run:
            logger.info("dry-run: %s", " ".join(command))
            return CommandResult(command, 0, "dry-run", "")
        stdout = ""
        stderr = ""
        try:
            result = subprocess.run(
                command,
                env=env,
                text=True,
                capture_output=capture,
                timeout=self.timeout_seconds,
                check=False,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            if check and result.returncode != 0:
                raise WineExecutorError(
                    f"Command failed (exit {result.returncode}): {' '.join(command)}\n{stderr.strip()}"
                )
            if stdout and not self.silent:
                logger.debug(stdout.strip())
            return CommandResult(command, result.returncode, stdout, stderr)
        except subprocess.TimeoutExpired as exc:  # pragma: no cover
            raise WineExecutorError(f"Command timed out: {' '.join(command)}") from exc

    def _resolve_wine_binary(self) -> Path:
        preferred = os.environ.get("AFFINITY_WINE_BIN") or os.environ.get("AFFINITY_CLI_WINE")
        candidates: List[Optional[str]] = [preferred, "wine64", "wine"]
        for candidate in candidates:
            if not candidate:
                continue
            resolved = shutil.which(candidate)
            if resolved:
                return Path(resolved)
        raise WineExecutorError(
            "Wine executable was not found. Install wine64 or set AFFINITY_CLI_WINE to a custom binary."
        )

    def _support_binary(self, name: str) -> str:
        candidate = self.wine_binary.parent / name
        if candidate.exists():
            return str(candidate)
        fallback = shutil.which(name)
        if fallback:
            return fallback
        return name

    def _build_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env["WINEPREFIX"] = str(self.prefix_path)
        env.setdefault("WINEDEBUG", "-all")
        env.setdefault("WINEARCH", "win64")
        env.setdefault("WINE_RENDERER", "vulkan")  # match AffinityOnLinux guidance (renderer=vulkan)
        return env

    def check_windows_version(self) -> None:
        """Ensure Wine reports a supported Windows version (10/11) before install."""
        env = self._build_env()
        try:
            res = subprocess.run(
                [str(self.wine_binary), "cmd", "/c", "ver"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as exc:
            raise WineExecutorError(f"Failed to query Windows version: {exc}") from exc

        output = (res.stdout or "") + (res.stderr or "")
        if "Version 10." in output or "Version 11." in output:
            return
        raise WineExecutorError(
            f"Wine reports unsupported Windows version. Output:\n{output.strip()}\n"
            "Set the prefix to Windows 10/11 and retry."
        )


__all__ = ["WineExecutor", "WineExecutorError", "CommandResult"]
