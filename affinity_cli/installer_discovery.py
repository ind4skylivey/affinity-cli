"""Installer discovery utilities for the universal installer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from packaging.version import Version

INSTALLER_PATTERN = re.compile(
    r"affinity[_-]?universal[_-]?([0-9]+\.[0-9]+\.[0-9]+)?\.exe",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InstallerInfo:
    file_version: str
    path: Path

    @property
    def label(self) -> str:
        return f"Affinity Universal ({self.file_version})"


class InstallerDiscovery:
    """Discover universal installers inside a directory."""

    def __init__(self, directory: Path):
        self.directory = directory

    def scan(self) -> List[InstallerInfo]:
        if not self.directory.exists():
            return []
        installers: List[InstallerInfo] = []
        for file in self.directory.iterdir():
            if not file.is_file():
                continue
            match = INSTALLER_PATTERN.search(file.name)
            if not match:
                continue
            version = match.group(1) or "unversioned"
            installers.append(InstallerInfo(file_version=version, path=file))
        installers.sort(key=lambda item: Version(item.file_version.replace("unversioned", "0.0.0")))
        return installers

    def select_installer(self) -> InstallerInfo:
        candidates = self.scan()
        if not candidates:
            raise FileNotFoundError(f"No Affinity Universal installers in {self.directory}")
        return candidates[-1]

    def summary(self) -> List[InstallerInfo]:
        return self.scan()


__all__ = ["InstallerDiscovery", "InstallerInfo"]
