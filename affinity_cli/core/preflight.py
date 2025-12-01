"""Pre-flight environment checks before download/install."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from affinity_cli import config
from affinity_cli.core.distro_detector import DistroDetector
from affinity_cli.utils.logger import logger

MIN_FREE_DEFAULT = 5 * 1024 * 1024 * 1024  # 5 GB


@dataclass
class PreflightIssue:
    level: str  # "error" or "warning"
    message: str
    hint: Optional[str] = None


@dataclass
class PreflightReport:
    ok: bool
    issues: List[PreflightIssue]

    @property
    def errors(self) -> List[PreflightIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> List[PreflightIssue]:
        return [i for i in self.issues if i.level == "warning"]


class PreflightChecker:
    """Runs a sequence of environment checks and aggregates results."""

    def __init__(
        self,
        *,
        cache_dir: Path = config.CACHE_DIR,
        min_free_bytes: int = MIN_FREE_DEFAULT,
    ) -> None:
        self.cache_dir = Path(cache_dir).expanduser()
        self.min_free_bytes = min_free_bytes

    def run(self) -> PreflightReport:
        issues: List[PreflightIssue] = []
        issues.extend(self._check_disk_space())
        issues.extend(self._check_cache_dir())
        issues.extend(self._check_wine_proton())
        issues.extend(self._check_gpu_vulkan())
        issues.extend(self._check_distro())
        ok = not any(i.level == "error" for i in issues)
        return PreflightReport(ok=ok, issues=issues)

    # --------------------------------------------
    # Individual checks
    # --------------------------------------------
    def _check_disk_space(self) -> List[PreflightIssue]:
        try:
            usage = shutil.disk_usage(self.cache_dir)
            if usage.free < self.min_free_bytes:
                needed_gb = round(self.min_free_bytes / (1024 ** 3))
                return [
                    PreflightIssue(
                        "error",
                        f"Not enough free space in {self.cache_dir.anchor or self.cache_dir}: "
                        f"{usage.free / (1024 ** 3):.1f} GB available, {needed_gb} GB required.",
                        "Free up disk space or set --cache-dir to a drive with more capacity.",
                    )
                ]
        except FileNotFoundError:
            return [
                PreflightIssue(
                    "error",
                    f"Path {self.cache_dir} does not exist and could not be inspected for free space.",
                    "Create the path or choose a different cache directory.",
                )
            ]
        except OSError as exc:
            return [PreflightIssue("warning", f"Could not read disk usage: {exc}")]
        return []

    def _check_cache_dir(self) -> List[PreflightIssue]:
        issues: List[PreflightIssue] = []
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return [
                PreflightIssue(
                    "error",
                    f"Cache directory {self.cache_dir} is not writable: {exc}",
                    "Adjust permissions or choose a different cache directory.",
                )
            ]

        if not os.access(self.cache_dir, os.W_OK):
            issues.append(
                PreflightIssue(
                    "error",
                    f"Cache directory {self.cache_dir} is not writable.",
                    "Run with a writable cache directory or adjust permissions.",
                )
            )

        try:
            mode = stat.S_IMODE(self.cache_dir.stat().st_mode)
            if mode != 0o700:
                issues.append(
                    PreflightIssue(
                        "warning",
                        f"Cache directory permissions are {oct(mode)}, recommended 0o700.",
                        "Run: chmod 700 ~/.cache/affinity-cli",
                    )
                )
        except OSError:
            pass

        return issues

    def _check_wine_proton(self) -> List[PreflightIssue]:
        preferred = os.environ.get("AFFINITY_CLI_WINE")
        candidates = [preferred, "wine64", "wine", "proton", "proton-run"]
        for candidate in candidates:
            if not candidate:
                continue
            resolved = shutil.which(candidate)
            if resolved:
                logger.debug("Using wine/proton candidate: %s -> %s", candidate, resolved)
                return []
        return [
            PreflightIssue(
                "error",
                "Wine/Proton runtime not found in PATH.",
                "Install wine64 (or Proton-GE) and ensure it is on PATH, or set AFFINITY_CLI_WINE.",
            )
        ]

    def _check_gpu_vulkan(self) -> List[PreflightIssue]:
        issues: List[PreflightIssue] = []

        gpu_vendor = self._detect_gpu_vendor()
        if gpu_vendor:
            logger.debug("Detected GPU vendor: %s", gpu_vendor)

        if not shutil.which("vulkaninfo"):
            issues.append(
                PreflightIssue(
                    "warning",
                    "Vulkan utilities not found (vulkaninfo missing).",
                    "Install Vulkan drivers for your GPU (e.g., mesa-vulkan-drivers, nvidia-utils).",
                )
            )
        return issues

    def _detect_gpu_vendor(self) -> Optional[str]:
        lspci = shutil.which("lspci")
        if not lspci:
            return None
        try:
            result = subprocess.run(
                [lspci, "-nnk"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return None
            text = result.stdout.lower()
            if "nvidia" in text:
                return "nvidia"
            if "amd" in text or "ati" in text:
                return "amd"
            if "intel" in text:
                return "intel"
        except Exception:
            return None
        return None

    def _check_distro(self) -> List[PreflightIssue]:
        issues: List[PreflightIssue] = []
        detector = DistroDetector()
        info = detector.get_distro_info()
        pm_cmd = info.get("package_manager")
        if not pm_cmd or pm_cmd == "unknown":
            issues.append(
                PreflightIssue(
                    "warning",
                    "Could not determine package manager for your distribution.",
                    "Install Wine and Vulkan manually for your distro.",
                )
            )
        else:
            if not shutil.which(pm_cmd):
                issues.append(
                    PreflightIssue(
                        "warning",
                        f"Package manager '{pm_cmd}' not found in PATH.",
                        f"Install or configure {pm_cmd} to allow dependency installation.",
                    )
                )
        return issues


__all__ = ["PreflightChecker", "PreflightReport", "PreflightIssue"]
