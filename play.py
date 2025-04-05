#!/usr/bin/env python3
"""Run the cat platformer game with Python version check."""

import sys
import importlib.util
import subprocess

# First, check if Python 3.12 is being used
if sys.version_info[:2] != (3, 12):
    print(
        f"Error: Python 3.12 is required, but you're using Python {sys.version_info.major}.{sys.version_info.minor}"
    )
    print(
        "Please install Python 3.12 or use a tool like pyenv to manage Python versions."
    )
    print("You can use pyenv with the .python-version file provided in this project.")
    sys.exit(1)

# Check if pygame is installed
if importlib.util.find_spec("pygame") is None:
    print("Pygame is not installed. Installing now...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pygame==2.5.2"], check=True
        )
        print("Pygame installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install Pygame. Please install it manually with:")
        print("  pip install pygame==2.5.2")
        sys.exit(1)

# Run the game
try:
    from cat_platformer.__main__ import main

    main()
except ImportError:
    print("Error: Game files not found. Make sure you've installed the package:")
    print("  pip install -e .")
    sys.exit(1)
