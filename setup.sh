#!/bin/bash

# Check if Python 3.12 is installed using our script
if ! python check_python_version.py; then
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -fsSL https://astral.sh/uv/install.sh | bash
    # Source the shell configuration to make uv available
    source ~/.bashrc
fi

# Create a virtual environment with Python 3.12
echo "Creating virtual environment with Python 3.12..."
uv venv --python=python3.12

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

echo "Setup complete! You can now run the game with: python cat_platformer_game.py"
echo "To activate the environment in the future, run: source .venv/bin/activate" 