"""Installer discovery helpers for the universal Affinity installer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set

from affinity_cli import config

UNIVERSAL_PATTERN = re.compile(r"affinity[_-]?universal.*\.exe$", re.IGNORECASE)


@dataclass(frozen=True)
class InstallerCandidate:
    """Represents a single universal installer on disk."""

    path: Path
    version_label: str
    size_bytes: int
    source: Path

    @property
    def human_size(self) -> str:
        size = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024
        return f"{size:.1f} GB"


class InstallerScanner:
    """Locate the Affinity Universal installer in one or more locations."""

    def __init__(self, *search_roots: Path):
        roots = search_roots or (config.DEFAULT_INSTALLERS_PATH,)
        self.search_roots: List[Path] = [Path(root).expanduser() for root in roots]

    def scan(self) -> List[InstallerCandidate]:
        candidates: List[InstallerCandidate] = []
        seen: Set[Path] = set()
        for root in self.search_roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path in seen:
                    continue
                if not self._is_universal_installer(path):
                    continue
                seen.add(path)
                candidates.append(
                    InstallerCandidate(
                        path=path,
                        version_label=self._extract_version(path.name) or "unversioned",
                        size_bytes=self._safe_size(path),
                        source=root,
                    )
                )
        candidates.sort(key=lambda c: (c.path.name.lower(), c.path))
        return candidates

    def first(self) -> Optional[InstallerCandidate]:
        """Return the first matching installer, or None."""
        candidates = self.scan()
        return candidates[0] if candidates else None

    @staticmethod
    def _is_universal_installer(path: Path) -> bool:
        return (
            path.suffix.lower() == ".exe"
            and UNIVERSAL_PATTERN.search(path.name) is not None
        )

    @staticmethod
    def _extract_version(filename: str) -> Optional[str]:
        match = re.search(r"(\d+\.\d+\.\d+)", filename)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _safe_size(path: Path) -> int:
        try:
            return path.stat().st_size
        except OSError:
            return 0


__all__ = ["InstallerScanner", "InstallerCandidate"]
