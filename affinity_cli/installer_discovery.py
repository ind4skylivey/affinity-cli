"""Installer discovery utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional

from packaging.version import Version

PRODUCT_NAMES = {
    "photo": "Affinity Photo",
    "designer": "Affinity Designer",
    "publisher": "Affinity Publisher",
}

INSTALLER_PATTERN = re.compile(
    r"^affinity-(photo|designer|publisher)(-msi)?-([0-9]+\.[0-9]+\.[0-9]+)\.exe$",
    re.IGNORECASE,
)

VersionLiteral = Literal["v1", "v2"]


@dataclass(frozen=True)
class InstallerInfo:
    product: str
    version: VersionLiteral
    file_version: str
    path: Path

    @property
    def label(self) -> str:
        return f"{PRODUCT_NAMES[self.product]} {self.version.upper()} ({self.file_version})"


class InstallerDiscovery:
    """Discover installers inside a directory."""

    def __init__(self, directory: Path):
        self.directory = directory

    def scan(self) -> List[InstallerInfo]:
        if not self.directory.exists():
            return []
        installers: List[InstallerInfo] = []
        for file in self.directory.iterdir():
            if not file.is_file():
                continue
            match = INSTALLER_PATTERN.match(file.name)
            if not match:
                continue
            product, msi_marker, file_version = match.groups()
            version: VersionLiteral = "v2" if msi_marker else "v1"
            installers.append(
                InstallerInfo(
                    product=product.lower(),
                    version=version,
                    file_version=file_version,
                    path=file,
                )
            )
        installers.sort(
            key=lambda item: (item.product, item.version, Version(item.file_version))
        )
        return installers

    def select_installer(
        self,
        product: str,
        preferred_version: Optional[VersionLiteral] = None,
    ) -> InstallerInfo:
        candidates = [inst for inst in self.scan() if inst.product == product]
        if not candidates:
            raise FileNotFoundError(
                f"No installers found for {PRODUCT_NAMES[product]} in {self.directory}"
            )
        if preferred_version:
            preferred = [inst for inst in candidates if inst.version == preferred_version]
            if not preferred:
                raise FileNotFoundError(
                    f"Installers for {PRODUCT_NAMES[product]} exist but not for {preferred_version}"
                )
            return preferred[-1]
        # prefer v2, fallback to v1
        v2 = [inst for inst in candidates if inst.version == "v2"]
        if v2:
            return v2[-1]
        return candidates[-1]

    def summary(self) -> Dict[str, List[InstallerInfo]]:
        result: Dict[str, List[InstallerInfo]] = {key: [] for key in PRODUCT_NAMES}
        for installer in self.scan():
            result[installer.product].append(installer)
        return result


__all__ = ["InstallerDiscovery", "InstallerInfo", "PRODUCT_NAMES", "VersionLiteral"]
