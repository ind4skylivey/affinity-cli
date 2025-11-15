"""Installer discovery and metadata helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from affinity_cli import config

VERSION_RE = re.compile(r"(?P<prefix>v)?(?P<version>\d+(?:\.\d+)+)")
PRODUCT_ALIASES: Dict[str, List[str]] = {
    "photo": ["photo", "aphoto", "affinityphoto"],
    "designer": ["designer", "adesigner", "affinitydesigner"],
    "publisher": ["publisher", "apublisher", "affinitypublisher"],
}


@dataclass(frozen=True)
class InstallerCandidate:
    product: str
    version_type: str
    version_label: str
    path: Path
    size_bytes: int

    @property
    def human_size(self) -> str:
        size = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024
        return f"{size:.1f} GB"


class InstallerScanner:
    def __init__(self, search_root: Path):
        self.search_root = Path(search_root).expanduser()

    def scan(self) -> List[InstallerCandidate]:
        if not self.search_root.exists():
            return []
        candidates: List[InstallerCandidate] = []
        for path in self.search_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in config.INSTALLER_SUFFIXES:
                continue
            candidate = self._parse_candidate(path)
            if candidate:
                candidates.append(candidate)
        candidates.sort(key=lambda c: (c.product, c.version_type, c.version_label, c.path.name.lower()))
        return candidates

    def select(self, products: Iterable[str], version: str) -> Dict[str, InstallerCandidate]:
        product_list = [self._normalize_product(p) for p in products]
        available = self.scan()
        selection: Dict[str, InstallerCandidate] = {}
        for product in product_list:
            candidate = self._pick_candidate(available, product, version)
            if candidate:
                selection[product] = candidate
        return selection

    def _pick_candidate(
        self, candidates: List[InstallerCandidate], product: str, version: str
    ) -> Optional[InstallerCandidate]:
        for candidate in candidates:
            if candidate.product == product and candidate.version_type == version:
                return candidate
        return None

    def _parse_candidate(self, path: Path) -> Optional[InstallerCandidate]:
        tokens = re.split(r"[^a-z0-9]+", path.stem.lower())
        if config.INSTALLER_NAME_PREFIX not in tokens:
            return None
        product = self._extract_product(tokens)
        if not product:
            return None
        version_label = self._extract_version(path.name)
        if not version_label:
            return None
        version_type = self._infer_version_type(version_label, tokens)
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        return InstallerCandidate(
            product=product,
            version_type=version_type,
            version_label=version_label,
            path=path,
            size_bytes=size,
        )

    def _extract_product(self, tokens: List[str]) -> Optional[str]:
        for product, aliases in PRODUCT_ALIASES.items():
            if any(alias in tokens for alias in aliases):
                return product
        return None

    @staticmethod
    def _extract_version(filename: str) -> Optional[str]:
        match = VERSION_RE.search(filename)
        if not match:
            return None
        return match.group("version")

    @staticmethod
    def _infer_version_type(version_label: str, tokens: List[str]) -> str:
        major = int(version_label.split(".")[0])
        if major >= 2 or "msi" in tokens or "v2" in tokens:
            return "v2"
        return "v1"

    @staticmethod
    def _normalize_product(product: str) -> str:
        product = product.strip().lower()
        if product == "all":
            raise ValueError("'all' is not a product identifier")
        if product not in config.AFFINITY_PRODUCTS:
            raise ValueError(f"Unknown product: {product}")
        return product


__all__ = ["InstallerScanner", "InstallerCandidate"]
