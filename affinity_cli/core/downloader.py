"""Smart downloader for the Affinity Universal installer."""

from __future__ import annotations

import getpass
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rich.console import Console
from tqdm.auto import tqdm

from affinity_cli import config
from affinity_cli.utils.logger import logger

UNIVERSAL_UPDATE_URL = "https://store.serif.com/update/windows/universal/"
DEFAULT_TIMEOUT = 30  # seconds
CONFIG_URL_FILE = config.CONFIG_DIR / "download_url.txt"


class DownloadError(RuntimeError):
    """Raised when the installer cannot be downloaded."""


@dataclass
class DownloadResult:
    path: Path
    source: str
    checksum_ok: bool


def _build_session(user_agent: str) -> Session:
    """Create a proxy-aware session with retries and sane defaults."""
    sess = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["HEAD", "GET", "OPTIONS", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retries)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    sess.trust_env = True  # honors HTTP(S)_PROXY, NO_PROXY, SSL_CERT_FILE, etc.
    sess.headers["User-Agent"] = user_agent
    return sess


class SmartDownloader:
    """Resilient downloader with public and authenticated strategies."""

    def __init__(self, *, session: Optional[Session] = None, console: Optional[Console] = None) -> None:
        self.console = console or Console()
        user_agent = f"affinity-cli/{config.VERSION}"
        self.session = session or _build_session(user_agent)

    def ensure_universal(
        self,
        destination: Optional[Path] = None,
        *,
        download_url: Optional[str] = None,
        configured_url: Optional[str] = None,
        expected_sha256: Optional[str] = None,
    ) -> Path:
        """
        Ensure the universal installer exists on disk, downloading it if needed.

        Args:
            destination: Optional override path. Defaults to ~/.cache/affinity-cli/Affinity_Universal.exe
            download_url: Optional direct URL override (non-interactive friendly).
            expected_sha256: Optional checksum to verify the downloaded file.

        Returns:
            Path to the installer file.
        """
        dest = destination or config.CACHE_DIR / config.UNIVERSAL_INSTALLER_FILENAME
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and dest.stat().st_size > 0:
            if expected_sha256:
                if self._verify_checksum(dest, expected_sha256):
                    logger.info("Using cached installer at %s (checksum OK)", dest)
                    return dest
                logger.warning("Cached installer failed checksum, re-downloading.")
                dest.unlink(missing_ok=True)
            else:
                logger.info("Using cached installer at %s", dest)
                return dest

        url, source = self._resolve_url(
            provided_url=download_url,
            configured_url=configured_url,
        )
        self.console.print(f"[cyan]Downloading Affinity Universal installer ({source})...[/cyan]")
        self._stream_to_file(url, dest, expected_sha256=expected_sha256)
        if source == "provided":
            self._persist_download_url(url)
        self.console.print(f"[green]Saved to {dest}[/green]")
        return dest

    # ------------------------------------------------------------------ #
    # URL resolution helpers
    # ------------------------------------------------------------------ #
    def _resolve_url(self, provided_url: Optional[str], configured_url: Optional[str]) -> Tuple[str, str]:
        if provided_url:
            return provided_url, "provided"
        if configured_url:
            return configured_url, "config"

        if CONFIG_URL_FILE.exists():
            try:
                saved = CONFIG_URL_FILE.read_text(encoding="utf-8").strip()
                if saved:
                    return saved, "config"
            except OSError:
                pass

        if config.DEFAULT_UNIVERSAL_URL:
            return config.DEFAULT_UNIVERSAL_URL, "official"

        url = self._strategy_public()
        if url:
            return url, "public"

        url = self._strategy_authenticated()
        if url:
            return url, "authenticated"

        raise DownloadError(
            "Unable to locate Affinity Universal download URL. Provide --download-url or check connectivity."
        )

    # ------------------------------------------------------------------ #
    # Strategy A: unauthenticated scrape
    # ------------------------------------------------------------------ #
    def _strategy_public(self) -> Optional[str]:
        for probe in (UNIVERSAL_UPDATE_URL,):
            try:
                response = self.session.get(probe, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
                response.raise_for_status()
            except requests.RequestException as exc:
                logger.debug("Public probe failed: %s", exc)
                continue

            if response.url.lower().endswith(".exe"):
                return response.url

            link = self._extract_download_link(response.text)
            if link:
                return link
        return None

    @staticmethod
    def _extract_download_link(html: str) -> Optional[str]:
        matches = re.findall(
            r"https?://[^\s\"'>]*Affinity[_-]?Universal[^\s\"'>]*\.exe",
            html,
            flags=re.IGNORECASE,
        )
        return matches[0] if matches else None

    # ------------------------------------------------------------------ #
    # Strategy B: authenticated session
    # ------------------------------------------------------------------ #
    def _strategy_authenticated(self) -> Optional[str]:
        email = os.getenv("AFFINITY_CLI_EMAIL")
        password = os.getenv("AFFINITY_CLI_PASSWORD")

        if not email or not password:
            if not sys.stdin.isatty():
                raise DownloadError(
                    "Login required but stdin is non-interactive. "
                    "Set AFFINITY_CLI_EMAIL and AFFINITY_CLI_PASSWORD or pass --download-url."
                )
            self.console.print(
                "[yellow]Public download failed. Affinity CLI first tries the official Affinity Universal URL.[/yellow]\n"
                "If it is blocked or has changed, retry with --download-url <URL>. Login-based auth is experimental and only used as a last resort."
            )
            email = self.console.input("Serif/Affinity account email: ").strip()
            password = getpass.getpass("Password: ").strip()

        if not email or not password:
            raise DownloadError("Email and password are required for authenticated download.")

        if not self._login(email, password):
            raise DownloadError(
                "Authentication failed with the Serif store. Check credentials or provide --download-url."
            )

        return self._strategy_public()

    def _login(self, email: str, password: str) -> bool:
        api_endpoints = [
            "https://store.serif.com/api/v1/auth/login/",
            "https://store.serif.com/api/auth/login/",
        ]

        for endpoint in api_endpoints:
            try:
                resp = self.session.post(
                    endpoint,
                    json={"email": email, "password": password},
                    timeout=DEFAULT_TIMEOUT,
                )
                if resp.status_code in (200, 201, 204):
                    logger.info("Authenticated via %s", endpoint)
                    return True
            except requests.RequestException as exc:
                logger.debug("API login failed against %s: %s", endpoint, exc)

        # Form-based fallback
        try:
            signin = self.session.get("https://store.serif.com/en-US/account/sign-in/", timeout=DEFAULT_TIMEOUT)
            token = self._extract_csrf(signin.text)
            if token:
                resp = self.session.post(
                    signin.url,
                    data={
                        "email": email,
                        "username": email,
                        "password": password,
                        "csrfmiddlewaretoken": token,
                    },
                    headers={"Referer": signin.url},
                    timeout=DEFAULT_TIMEOUT,
                    allow_redirects=True,
                )
                if resp.status_code in (200, 302):
                    logger.info("Authenticated via form login")
                    return True
        except requests.RequestException as exc:
            logger.debug("Form login failed: %s", exc)

        return False

    @staticmethod
    def _extract_csrf(html: str) -> Optional[str]:
        match = re.search(r'name=[\"\\\']csrfmiddlewaretoken[\"\\\'] value=[\"\\\']([^\"\\\']+)', html)
        return match.group(1) if match else None

    # ------------------------------------------------------------------ #
    # Download helper
    # ------------------------------------------------------------------ #
    def _stream_to_file(self, url: str, destination: Path, *, expected_sha256: Optional[str]) -> None:
        resume_pos = destination.stat().st_size if destination.exists() else 0
        headers = {"Range": f"bytes={resume_pos}-"} if resume_pos else {}
        hasher = hashlib.sha256()
        try:
            with self.session.get(url, stream=True, timeout=DEFAULT_TIMEOUT, headers=headers) as response:
                if response.status_code in (416,):
                    destination.unlink(missing_ok=True)
                    resume_pos = 0
                    headers = {}
                    return self._stream_to_file(url, destination, expected_sha256=expected_sha256)

                response.raise_for_status()
                total = int(response.headers.get("content-length", 0))
                if total == 0:
                    logger.warning("Server did not provide content-length; download progress may be inaccurate.")
                chunk_size = 1024 * 128
                progress = tqdm(
                    total=total + resume_pos if total else None,
                    unit="B",
                    unit_scale=True,
                    desc="Downloading",
                    disable=not self.console.is_terminal,
                    initial=resume_pos,
                )
                mode = "ab" if resume_pos else "wb"
                with destination.open(mode) as handle:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        handle.write(chunk)
                        hasher.update(chunk)
                        progress.update(len(chunk))
                progress.close()
        except requests.RequestException as exc:
            hint = "Check your connection or proxy settings (HTTP(S)_PROXY/NO_PROXY)." if "Proxy" in str(exc) else ""
            raise DownloadError(f"Download failed: {exc}. {hint}".strip()) from exc

        if expected_sha256:
            if not self._verify_checksum(destination, expected_sha256, precomputed=hasher.hexdigest()):
                destination.unlink(missing_ok=True)
                raise DownloadError("Checksum mismatch after download; file removed.")

    @staticmethod
    def _verify_checksum(path: Path, expected: str, *, precomputed: Optional[str] = None) -> bool:
        expected = expected.lower().strip()
        if precomputed:
            return precomputed.lower() == expected
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 256), b""):
                hasher.update(chunk)
        return hasher.hexdigest().lower() == expected

    def _persist_download_url(self, url: str) -> None:
        """
        Persist the provided download URL so future runs can reuse it automatically.
        Stored in a simple text file under config dir to avoid clobbering user config formats.
        """
        try:
            CONFIG_URL_FILE.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_URL_FILE.write_text(url.strip(), encoding="utf-8")
            logger.info("Stored download URL for future installs: %s", url)
        except OSError as exc:
            logger.debug("Could not persist download URL: %s", exc)


__all__ = ["SmartDownloader", "DownloadError", "DownloadResult"]
