"""Tests for installer scanner logic (universal model)."""

from pathlib import Path

from affinity_cli.core.installer_scanner import InstallerScanner


def _touch(path: Path) -> None:
    path.write_bytes(b"binary-data")


def test_scan_detects_universal_installer(tmp_path):
    installer = tmp_path / "Affinity_Universal_2.5.0.exe"
    _touch(installer)

    scanner = InstallerScanner(tmp_path)
    candidates = scanner.scan()

    assert len(candidates) == 1
    assert candidates[0].path == installer
    assert candidates[0].version_label == "2.5.0"


def test_scan_ignores_non_matching_files(tmp_path):
    garbage = tmp_path / "affinity-photo-legacy.exe"
    other = tmp_path / "random.txt"
    _touch(garbage)
    other.write_text("noop")

    scanner = InstallerScanner(tmp_path)
    assert scanner.scan() == []


def test_first_returns_none_when_missing(tmp_path):
    scanner = InstallerScanner(tmp_path)
    assert scanner.first() is None
