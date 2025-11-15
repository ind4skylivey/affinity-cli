"""
Setup script for Affinity CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="affinity-cli",
    version="1.1.0",
    author="ind4skylivey",
    description="Universal CLI installer for Affinity products on Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ind4skylivey/affinity-cli",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "tomli; python_version < '3.11'",
    ],
    entry_points={
        "console_scripts": [
            "affinity-cli=affinity_cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Installation/Setup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
    keywords="affinity wine linux installer cli photo designer publisher",
    project_urls={
        "Bug Reports": "https://github.com/ind4skylivey/affinity-cli/issues",
        "Source": "https://github.com/ind4skylivey/affinity-cli",
    },
)
