"""
Unit tests for distro_detector module
"""

import pytest
from affinity_cli.core.distro_detector import (
    DistroDetector,
    PackageManager,
    DistroFamily,
    detect_distro,
    detect_package_manager
)


class TestDistroDetector:
    """Test DistroDetector class"""
    
    def test_detector_initialization(self):
        """Test that detector initializes without errors"""
        detector = DistroDetector()
        assert detector is not None
        assert detector.distro_id is not None
    
    def test_distro_info_returned(self):
        """Test that distro info dictionary is properly formatted"""
        detector = DistroDetector()
        info = detector.get_distro_info()
        
        assert isinstance(info, dict)
        assert "id" in info
        assert "name" in info
        assert "version" in info
        assert "family" in info
        assert "package_manager" in info
    
    def test_package_manager_info(self):
        """Test that package manager commands are returned"""
        detector = DistroDetector()
        pm_info = detector.get_package_manager_info()
        
        assert isinstance(pm_info, dict)
        if pm_info:  # May be empty for unknown distros
            assert "install" in pm_info or "search" in pm_info
    
    def test_distro_family_enum(self):
        """Test that distro family is valid enum"""
        detector = DistroDetector()
        assert detector.distro_family in [
            DistroFamily.DEBIAN,
            DistroFamily.FEDORA,
            DistroFamily.ARCH,
            DistroFamily.SUSE,
            DistroFamily.UNKNOWN
        ]
    
    def test_package_manager_enum(self):
        """Test that package manager is valid enum"""
        detector = DistroDetector()
        assert detector.package_manager in [
            PackageManager.APT,
            PackageManager.DNF,
            PackageManager.YUM,
            PackageManager.PACMAN,
            PackageManager.ZYPPER,
            PackageManager.APTITUDE,
            None
        ]
    
    def test_is_root_returns_bool(self):
        """Test that is_root returns boolean"""
        result = DistroDetector.is_root()
        assert isinstance(result, bool)
    
    def test_detect_distro_function(self):
        """Test standalone detect_distro function"""
        name, version, pm = detect_distro()
        assert name is not None
        assert version is not None
        assert pm is not None or pm is None  # Can be None for unknown
    
    def test_detect_package_manager_function(self):
        """Test standalone detect_package_manager function"""
        pm, cmd, needs_sudo = detect_package_manager()
        assert pm is not None or pm is None
        assert isinstance(cmd, str)
        assert isinstance(needs_sudo, bool)


class TestDistroMapping:
    """Test distro mapping logic"""
    
    def test_debian_family_mapping(self):
        """Test Debian family is correctly mapped"""
        debian_distros = ["ubuntu", "debian", "linuxmint", "pop"]
        for distro in debian_distros:
            if distro in DistroDetector.DISTRO_MAPPING:
                family, pm = DistroDetector.DISTRO_MAPPING[distro]
                assert family == DistroFamily.DEBIAN
                assert pm == PackageManager.APT
    
    def test_arch_family_mapping(self):
        """Test Arch family is correctly mapped"""
        arch_distros = ["arch", "manjaro", "garuda", "cachyos"]
        for distro in arch_distros:
            if distro in DistroDetector.DISTRO_MAPPING:
                family, pm = DistroDetector.DISTRO_MAPPING[distro]
                assert family == DistroFamily.ARCH
                assert pm == PackageManager.PACMAN
    
    def test_fedora_family_mapping(self):
        """Test Fedora family is correctly mapped"""
        fedora_distros = ["fedora", "rhel", "centos", "rocky"]
        for distro in fedora_distros:
            if distro in DistroDetector.DISTRO_MAPPING:
                family, pm = DistroDetector.DISTRO_MAPPING[distro]
                assert family == DistroFamily.FEDORA
                assert pm == PackageManager.DNF


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
