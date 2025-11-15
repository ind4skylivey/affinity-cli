"""Configuration handling for affinity-cli."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for <3.11
    import tomli as tomllib  # type: ignore[no-redef]

CONFIG_DIR = Path.home() / ".config" / "affinity-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_INSTALLERS_DIR = Path.cwd() / "affinity-installers"
DEFAULT_WINE_PREFIX = Path.home() / ".wine-affinity"
DEFAULT_VERSION = "v2"


@dataclass
class UserConfig:
    """Runtime configuration values."""

    installers_path: Path = field(default_factory=lambda: DEFAULT_INSTALLERS_DIR)
    wine_prefix: Path = field(default_factory=lambda: DEFAULT_WINE_PREFIX)
    default_version: str = DEFAULT_VERSION

    def with_overrides(
        self,
        installers_path: Optional[Path] = None,
        wine_prefix: Optional[Path] = None,
        default_version: Optional[str] = None,
    ) -> "UserConfig":
        data = {
            "installers_path": installers_path or self.installers_path,
            "wine_prefix": wine_prefix or self.wine_prefix,
            "default_version": (default_version or self.default_version).lower(),
        }
        return UserConfig(**data)

    def validate(self) -> None:
        if self.default_version not in {"v1", "v2"}:
            raise ValueError("default_version must be 'v1' or 'v2'")


class ConfigLoader:
    """Load configuration from disk and environment."""

    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> UserConfig:
        data: Dict[str, Any] = {}
        if self.config_file.exists():
            data = self._parse_file(self.config_file)
        cfg = UserConfig(
            installers_path=Path(data.get("installers_path", DEFAULT_INSTALLERS_DIR)),
            wine_prefix=Path(data.get("wine_prefix", DEFAULT_WINE_PREFIX)),
            default_version=str(data.get("default_version", DEFAULT_VERSION)).lower(),
        )
        env_override = self._load_from_env()
        overrides: Dict[str, Any] = {}
        if "installers_path" in env_override:
            overrides["installers_path"] = Path(env_override["installers_path"])
        if "wine_prefix" in env_override:
            overrides["wine_prefix"] = Path(env_override["wine_prefix"])
        if "default_version" in env_override:
            overrides["default_version"] = env_override["default_version"]
        if overrides:
            cfg = cfg.with_overrides(**overrides)
        cfg.validate()
        return cfg

    def _parse_file(self, file_path: Path) -> Dict[str, Any]:
        content = file_path.read_bytes()
        payload = tomllib.loads(content.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Configuration file must contain a table")
        return payload

    def _load_from_env(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        installers = os.getenv("AFFINITY_INSTALLERS_PATH")
        prefix = os.getenv("AFFINITY_WINE_PREFIX")
        version = os.getenv("AFFINITY_DEFAULT_VERSION")
        if installers:
            mapping["installers_path"] = installers
        if prefix:
            mapping["wine_prefix"] = prefix
        if version:
            mapping["default_version"] = version.lower()
        return mapping


__all__ = ["ConfigLoader", "UserConfig", "CONFIG_FILE", "CONFIG_DIR"]
