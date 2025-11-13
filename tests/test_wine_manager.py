"""
Unit tests for wine_manager module
"""

import pytest
from pathlib import Path
from affinity_cli.core.wine_manager import WineManager


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
