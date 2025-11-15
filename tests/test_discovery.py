from pathlib import Path

from affinity_cli.installer_discovery import InstallerDiscovery


def create_installer(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_bytes(b"dummy")


def test_scan_and_select(tmp_path):
    create_installer(tmp_path, "affinity-photo-1.10.6.exe")
    create_installer(tmp_path, "affinity-photo-msi-2.6.5.exe")
    create_installer(tmp_path, "affinity-designer-1.10.6.exe")

    discovery = InstallerDiscovery(tmp_path)
    installers = discovery.scan()
    assert len(installers) == 3

    selected_photo = discovery.select_installer("photo")
    assert selected_photo.version == "v2"

    selected_photo_v1 = discovery.select_installer("photo", "v1")
    assert selected_photo_v1.version == "v1"

    selected_designer = discovery.select_installer("designer")
    assert selected_designer.version == "v1"
