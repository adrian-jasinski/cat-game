#!/usr/bin/env python3
"""Check if the correct Python version is being used."""

import sys
import platform


def check_python_version():
    """Check if Python 3.12 is being used and print a message."""
    major, minor = sys.version_info[:2]

    if (major, minor) != (3, 12):
        print(
            f"Error: Python 3.12 is required, but you're using Python {major}.{minor}"
        )
        print(
            "Please install Python 3.12 or use a tool like pyenv to manage Python versions."
        )
        print(
            "You can use pyenv with the .python-version file provided in this project."
        )
        sys.exit(1)

    print(f"✓ Using Python {major}.{minor} - Correct version!")
    print(f"  Python executable: {sys.executable}")
    print(f"  System: {platform.system()} {platform.release()}")
    return True


if __name__ == "__main__":
    check_python_version()
