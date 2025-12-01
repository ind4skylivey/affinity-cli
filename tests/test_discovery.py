from pathlib import Path

from affinity_cli.installer_discovery import InstallerDiscovery


def create_installer(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_bytes(b"dummy")


def test_scan_and_select_universal(tmp_path):
    create_installer(tmp_path, "Affinity_Universal_2.5.0.exe")
    create_installer(tmp_path, "Affinity_Universal_2.6.1.exe")

    discovery = InstallerDiscovery(tmp_path)
    installers = discovery.scan()
    assert len(installers) == 2

    selected = discovery.select_installer()
    assert selected.file_version == "2.6.1"


def test_select_raises_when_missing(tmp_path):
    discovery = InstallerDiscovery(tmp_path)
    try:
        discovery.select_installer()
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        assert True
