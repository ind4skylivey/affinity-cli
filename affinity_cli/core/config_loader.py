"""User configuration loader and runtime resolver for Affinity CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from affinity_cli import config

try:  # Python 3.11+
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore

try:  # Optional dependency for YAML configs
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


class ConfigError(RuntimeError):
    """Raised when the configuration file cannot be processed."""


@dataclass(frozen=True)
class UserConfig:
    installers_path: Optional[Path] = None
    wine_prefix: Optional[Path] = None
    default_version: Optional[str] = None


@dataclass(frozen=True)
class ResolvedConfig:
    installers_path: Path
    wine_prefix: Path
    default_version: str

    def to_display_dict(self) -> Dict[str, str]:
        return {
            "Installers path": str(self.installers_path),
            "Wine prefix": str(self.wine_prefix),
            "Default installer version": self.default_version,
        }


class ConfigLoader:
    """Loads configuration from ~/.config/affinity-cli or an explicit path."""

    CONFIG_FILES = (
        "config.toml",
        "config.yaml",
        "config.yml",
        "config.json",
    )

    def __init__(self, explicit_path: Optional[str] = None) -> None:
        self.explicit_path = Path(explicit_path).expanduser() if explicit_path else None
        self.config_path: Optional[Path] = None
        self._raw_data: Dict[str, Any] = {}
        self.user_config = UserConfig()
        self._load()

    def derive(
        self,
        *,
        installers_path: Optional[str] = None,
        prefix_path: Optional[str] = None,
        version: Optional[str] = None,
    ) -> ResolvedConfig:
        installers = self._normalize_path(
            installers_path
            or (self.user_config.installers_path and str(self.user_config.installers_path))
            or str(config.DEFAULT_INSTALLERS_PATH)
        )
        prefix = self._normalize_path(
            prefix_path
            or (self.user_config.wine_prefix and str(self.user_config.wine_prefix))
            or str(config.DEFAULT_WINE_PREFIX)
        )
        version_choice = (version or self.user_config.default_version or config.DEFAULT_INSTALLER_VERSION)
        version_choice = version_choice.lower()
        if version_choice not in config.SUPPORTED_INSTALLER_VERSIONS:
            raise ConfigError(
                f"Invalid installer version '{version_choice}'. Supported values:"
                f" {', '.join(config.SUPPORTED_INSTALLER_VERSIONS)}"
            )
        return ResolvedConfig(installers_path=installers, wine_prefix=prefix, default_version=version_choice)

    def _load(self) -> None:
        if self.explicit_path:
            if not self.explicit_path.exists():
                raise ConfigError(f"Config file not found: {self.explicit_path}")
            self.config_path = self.explicit_path
            self._raw_data = self._read_file(self.explicit_path)
            self.user_config = self._parse_user_config(self._raw_data)
            return

        for candidate in self.CONFIG_FILES:
            path = config.CONFIG_DIR / candidate
            if path.exists():
                self.config_path = path
                self._raw_data = self._read_file(path)
                self.user_config = self._parse_user_config(self._raw_data)
                return

        self._raw_data = {}
        self.user_config = UserConfig()

    def _parse_user_config(self, payload: Dict[str, Any]) -> UserConfig:
        if not payload:
            return UserConfig()
        allowed = {"installers_path", "wine_prefix", "default_version"}
        unexpected = set(payload.keys()) - allowed
        if unexpected:
            raise ConfigError(f"Unknown configuration field(s): {', '.join(sorted(unexpected))}")
        installers = self._optional_path(payload.get("installers_path"))
        prefix = self._optional_path(payload.get("wine_prefix"))
        default_version = payload.get("default_version")
        if default_version is not None:
            if not isinstance(default_version, str):
                raise ConfigError("default_version must be a string (v1 or v2)")
            default_version = default_version.lower().strip()
            if default_version not in config.SUPPORTED_INSTALLER_VERSIONS:
                raise ConfigError(
                    f"default_version must be one of {', '.join(config.SUPPORTED_INSTALLER_VERSIONS)}"
                )
        return UserConfig(
            installers_path=installers,
            wine_prefix=prefix,
            default_version=default_version,
        )

    def _read_file(self, path: Path) -> Dict[str, Any]:
        suffix = path.suffix.lower()
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        if suffix == ".json":
            return self._as_dict(json.loads(text), path)
        if suffix == ".toml":
            if tomllib is None:
                raise ConfigError("Reading TOML configs requires the 'tomli' package on Python < 3.11")
            return self._as_dict(tomllib.loads(text), path)
        if suffix in {".yaml", ".yml"}:
            if yaml is None:
                raise ConfigError("PyYAML is required to parse YAML configuration files")
            return self._as_dict(yaml.safe_load(text) or {}, path)
        raise ConfigError(f"Unsupported config format: {path.suffix}")

    @staticmethod
    def _as_dict(value: Any, path: Path) -> Dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ConfigError(f"Configuration file {path} must be a mapping")
        return value

    @staticmethod
    def _normalize_path(raw_path: str) -> Path:
        return Path(raw_path).expanduser()

    @staticmethod
    def _optional_path(value: Any) -> Optional[Path]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ConfigError("Path values must be strings")
        return Path(value).expanduser()


__all__ = ["ConfigLoader", "ConfigError", "ResolvedConfig", "UserConfig"]
