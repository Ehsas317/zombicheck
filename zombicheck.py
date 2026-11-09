#!/usr/bin/env python3
"""Back-compat shim: python3 zombicheck.py ..."""

import sys

from zombicheck.cli import main

if __name__ == "__main__":
    sys.exit(main())
