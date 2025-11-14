"""Unit tests for wine_manager module"""

from pathlib import Path
import io
import tarfile

import pytest

from affinity_cli.core.wine_manager import WineManager


def _build_tar(tmp_path, member_name, *, member_type=tarfile.REGTYPE, data=b"test"):
    tar_path = tmp_path / "archive.tar"
    with tarfile.open(tar_path, "w") as tar:
        info = tarfile.TarInfo(name=member_name)
        info.type = member_type
        info.mtime = 0
        if member_type in (tarfile.REGTYPE, tarfile.AREGTYPE):
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        else:
            tar.addfile(info)
    return tar_path


class TestWineManager:
    """Test WineManager class"""
    
    def test_manager_initialization(self):
        """Test that manager initializes without errors"""
        manager = WineManager()
        assert manager is not None
        assert manager.wine_version == "latest"
    
    def test_wine_version_info_exists(self):
        """Test that Wine version info is properly structured"""
        manager = WineManager()
        assert manager.version_info is not None
        assert "version" in manager.version_info
        assert "urls" in manager.version_info
    
    def test_check_wine_installed_returns_bool(self):
        """Test that check_wine_installed returns boolean"""
        manager = WineManager()
        result = manager.check_wine_installed()
        assert isinstance(result, bool)
    
    def test_get_wine_path_returns_path_or_none(self):
        """Test that get_wine_path returns Path or None"""
        manager = WineManager()
        result = manager.get_wine_path()
        assert result is None or isinstance(result, Path)
    
    def test_get_wine_version_returns_string_or_none(self):
        """Test that get_wine_version returns string or None"""
        manager = WineManager()
        result = manager.get_wine_version()
        assert result is None or isinstance(result, str)
    
    def test_wine_dir_is_path(self):
        """Test that wine_dir is a Path object"""
        manager = WineManager()
        assert isinstance(manager.wine_dir, Path)
    
    def test_wine_bin_is_path(self):
        """Test that wine_bin is a Path object"""
        manager = WineManager()
        assert isinstance(manager.wine_bin, Path)
    
    def test_verify_integrity_returns_bool(self):
        """Test that verify_wine_integrity returns boolean"""
        manager = WineManager()
        fake_path = Path("/tmp/nonexistent.tar.xz")
        result = manager.verify_wine_integrity(fake_path)
        assert isinstance(result, bool)

    def test_extract_archive_rejects_traversal(self, tmp_path):
        """Ensure path traversal inside archives is rejected"""
        manager = WineManager(install_dir=tmp_path / "install")
        tar_path = _build_tar(tmp_path, "../evil.txt")

        success, message = manager._extract_archive(tar_path, manager.install_dir)

        assert not success
        assert "escapes" in message
        assert not (tmp_path / "evil.txt").exists()

    def test_extract_archive_rejects_special_files(self, tmp_path):
        """Ensure device nodes or other special files are not extracted"""
        manager = WineManager(install_dir=tmp_path / "install")
        tar_path = _build_tar(tmp_path, "devnode", member_type=tarfile.CHRTYPE)

        success, message = manager._extract_archive(tar_path, manager.install_dir)

        assert not success
        assert "special file" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
