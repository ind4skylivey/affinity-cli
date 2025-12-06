"""Affinity CLI package metadata."""

__version__ = "2.0.0"
__author__ = "ind4skylivey"
__license__ = "MIT"


def get_version() -> str:
    """Return the package version."""
    return __version__


__all__ = ["__version__", "get_version", "__author__", "__license__"]
