"""
Unit tests for dependency_manager module
"""

import pytest
from affinity_cli.core.dependency_manager import DependencyManager
from affinity_cli.core.distro_detector import DistroDetector


class TestDependencyManager:
    """Test DependencyManager class"""
    
    def test_manager_initialization(self):
        """Test that manager initializes without errors"""
        manager = DependencyManager()
        assert manager is not None
        assert manager.detector is not None
    
    def test_check_dependencies_returns_dict(self):
        """Test that check_dependencies returns dictionary"""
        manager = DependencyManager()
        status = manager.check_dependencies()
        
        assert isinstance(status, dict)
        for pkg, installed in status.items():
            assert isinstance(pkg, str)
            assert isinstance(installed, bool)
    
    def test_get_missing_dependencies_returns_list(self):
        """Test that get_missing_dependencies returns list"""
        manager = DependencyManager()
        missing = manager.get_missing_dependencies()
        
        assert isinstance(missing, list)
        for pkg in missing:
            assert isinstance(pkg, str)
    
    def test_verify_dependencies_returns_bool(self):
        """Test that verify_dependencies returns boolean"""
        manager = DependencyManager()
        result = manager.verify_dependencies()
        
        assert isinstance(result, bool)
    
    def test_debian_dependencies_list(self):
        """Test that Debian dependencies are properly defined"""
        manager = DependencyManager()
        deps = manager._get_debian_dependencies()
        
        assert isinstance(deps, list)
        assert len(deps) > 0
        assert "wine" in deps or "wine64" in deps
    
    def test_arch_dependencies_list(self):
        """Test that Arch dependencies are properly defined"""
        manager = DependencyManager()
        deps = manager._get_arch_dependencies()
        
        assert isinstance(deps, list)
        assert len(deps) > 0
        assert "wine" in deps
    
    def test_critical_dependencies_exist(self):
        """Test that critical dependencies are defined"""
        manager = DependencyManager()
        critical = manager._get_critical_dependencies()
        
        assert isinstance(critical, list)
        assert len(critical) > 0


class TestDependencyInstallation:
    """Test dependency installation methods"""
    
    def test_install_dependencies_signature(self):
        """Test that install_dependencies has correct signature"""
        manager = DependencyManager()
        
        # Should accept skip_multiarch parameter
        result = manager.install_dependencies(skip_multiarch=True)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
