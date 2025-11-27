"""Wine prefix management helpers."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from affinity_cli.core.wine_manager import WineManager


class PrefixManager:
    """
    Minimal manager for creating and checking a Wine prefix.

    This implementation intentionally keeps side effects small; it is enough for
    status checks and install flows while avoiding fragile assumptions.
    """

    def __init__(self, prefix_path: Path, wine_manager: Optional[WineManager] = None) -> None:
        self.prefix_path = Path(prefix_path).expanduser()
        self.wine_manager = wine_manager or WineManager()

    # ------------------------------------------------------------------
    # Basic introspection helpers
    # ------------------------------------------------------------------
    def prefix_exists(self) -> bool:
        """Return True when the prefix directory looks initialized."""
        return (self.prefix_path / "drive_c").exists()

    # ------------------------------------------------------------------
    # Creation helpers
    # ------------------------------------------------------------------
    def create_prefix(self) -> Tuple[bool, str]:
        """
        Initialize the Wine prefix using wineboot.

        Returns:
            (success flag, human-readable message)
        """
        wine_bin = self.wine_manager.get_wine_path()
        if not wine_bin:
            return False, "Wine binary not found; install Wine first."

        try:
            self.prefix_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - filesystem issues
            return False, f"Unable to create prefix directory: {exc}"

        env = os.environ.copy()
        env["WINEPREFIX"] = str(self.prefix_path)
        env.setdefault("WINEARCH", "win64")

        try:
            result = subprocess.run(
                [str(wine_bin), "wineboot", "-u"],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:  # pragma: no cover - rare
            return False, "wineboot timed out while initializing the prefix."
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"Failed to initialize prefix: {exc}"

        if result.returncode != 0:
            return False, f"wineboot failed: {result.stderr.strip() or result.stdout.strip()}"

        return True, f"Prefix initialized at {self.prefix_path}"


__all__ = ["PrefixManager"]
