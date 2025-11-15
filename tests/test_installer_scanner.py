"""Tests for installer scanner logic."""

from pathlib import Path

from affinity_cli.core.installer_scanner import InstallerScanner


def _touch(path: Path) -> None:
    path.write_bytes(b"binary-data")


def test_scan_detects_multiple_versions(tmp_path):
    photo_v1 = tmp_path / "affinity-photo-1.10.6.exe"
    designer_v2 = tmp_path / "Affinity-Designer-msi-2.6.5.EXE"
    publisher_v2 = tmp_path / "affinity_publisher_v2_2.3.1.exe"
    _touch(photo_v1)
    _touch(designer_v2)
    _touch(publisher_v2)

    scanner = InstallerScanner(tmp_path)
    candidates = scanner.scan()

    summary = {(c.product, c.version_type) for c in candidates}
    assert ("photo", "v1") in summary
    assert ("designer", "v2") in summary
    assert ("publisher", "v2") in summary


def test_select_filters_by_version(tmp_path):
    v1 = tmp_path / "affinity-designer-1.9.0.exe"
    v2 = tmp_path / "affinity-designer-msi-2.6.5.exe"
    _touch(v1)
    _touch(v2)

    scanner = InstallerScanner(tmp_path)
    selection_v1 = scanner.select(["designer"], "v1")
    selection_v2 = scanner.select(["designer"], "v2")

    assert selection_v1["designer"].version_label.startswith("1.")
    assert selection_v2["designer"].version_label.startswith("2.")


def test_scan_ignores_non_affinity_files(tmp_path):
    garbage = tmp_path / "not-affinity.exe"
    _touch(garbage)

    scanner = InstallerScanner(tmp_path)
    assert scanner.scan() == []
