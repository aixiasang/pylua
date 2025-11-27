#!/usr/bin/env python3
"""
PyLua - A Python implementation of Lua 5.3

This module allows running PyLua as a command:
    python -m pylua [options] [filenames]

For help:
    python -m pylua --help
"""

import sys
from .cli import main

if __name__ == '__main__':
    sys.exit(main())
