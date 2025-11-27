#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyLua Setup Script

A Python implementation of Lua 5.3.6 virtual machine.
Author: aixiasang
"""

from setuptools import setup, find_packages

setup(
    name="pylua",
    version="5.3.6",
    author="aixiasang",
    description="A Python implementation of Lua 5.3.6 virtual machine",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aixiasang/pylua",
    packages=find_packages(include=["pylua", "pylua.*"]),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov>=4.0"],
    },
    entry_points={
        "console_scripts": [
            "pylua=pylua.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Interpreters",
    ],
    keywords=["lua", "compiler", "virtual-machine", "bytecode", "interpreter"],
    license="MIT",
)
