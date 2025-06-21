#!/usr/bin/env python3
"""
Setup script for pycabfile - CAB file handling with zipfile-like interface
"""

from setuptools import setup, find_packages
import os


# Read README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "A Python library for handling Microsoft Cabinet files with zipfile-like interface"


setup(
    name="pycabfile",
    version="1.0.0",
    author="Kei Choi",
    author_email="hanul93@gmail.com",
    description="A Python library for handling Microsoft Cabinet files with zipfile-like interface",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/hanul93/pycabfile",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Archiving :: Compression",
    ],
    python_requires=">=3.10",
    install_requires=[
        # No external dependencies required - uses built-in modules only
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pycabfile-demo=example:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="cab cabinet archive compression",
    project_urls={
        "Bug Reports": "https://github.com/hanul93/pycabfile/issues",
        "Source": "https://github.com/hanul93/pycabfile",
        "Documentation": "https://github.com/hanul93/pycabfile/blob/main/README.md",
    },
)
