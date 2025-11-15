"""Wine execution helpers."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Iterable, List

from rich.console import Console

console = Console()


class WineExecutor:
    """Encapsulate wine command execution."""

    def __init__(self, prefix: Path, binary: str = "wine"):
        self.prefix = prefix
        self.binary = binary

    def run_installer(
        self,
        installer: Path,
        silent: bool = False,
        extra_args: Iterable[str] | None = None,
        dry_run: bool = False,
    ) -> int:
        args: List[str] = [self.binary, str(installer)]
        if silent:
            args.append("/quiet")
        if extra_args:
            args.extend(extra_args)
        env = os.environ.copy()
        env["WINEPREFIX"] = str(self.prefix)
        command = " ".join(shlex.quote(arg) for arg in args)
        console.print(f"[cyan]Executing:[/cyan] WINEPREFIX={self.prefix} {command}")
        if dry_run:
            console.print("[yellow]Dry-run enabled. Command not executed.[/yellow]")
            return 0
        self.prefix.mkdir(parents=True, exist_ok=True)
        process = subprocess.run(args, env=env, check=False)
        if process.returncode != 0:
            raise RuntimeError(
                f"Wine returned exit code {process.returncode}. Check the installer output."
            )
        return process.returncode


__all__ = ["WineExecutor"]
