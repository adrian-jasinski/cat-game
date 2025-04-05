# Cat Platformer Game

A simple 2D platformer game built with Pygame where a red cat jumps over obstacles.

## Features

- Animated cat character with different animations for running, jumping, falling, and death
- Beautiful multi-layered mountain dusk background with purple mountains and silhouetted trees
- Realistic natural obstacles (rocks, logs, bushes, and fallen trees)
- Detailed ground with grass, soil texture, and small flowers
- Particle effects for jumps and impacts
- Increasing difficulty as you progress
- Score tracking
- Death animations when you collide with obstacles

## Screenshots

The game features:
- Atmospheric dusk mountain background with parallax scrolling
- Silhouetted forest treeline against a dusk/night sky
- Detailed pixel-art animation for the cat character
- Dynamic lighting and particle effects
- Richly textured ground with details

## Requirements

- Python 3.12 (exact version, not higher)
- Pygame 2.5.2

## Python Version

This project requires **exactly Python 3.12**, not higher or lower. A `.python-version` file is included for tools like pyenv to automatically select the correct version.

You can verify your Python version with:

```bash
python --version
```

Or use the included version check script:

```bash
python check_python_version.py
```

## Quick Start

The easiest way to play is using the play.py script, which checks Python version and handles pygame installation:

```bash
./play.py
```

OR

```bash
python play.py
```

## Quick Setup

Use the provided setup scripts for easy installation:

- On Linux/macOS:
  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```

- On Windows:
  ```
  setup.bat
  ```

## Running the Game

After installation, you can run the game in several ways:

1. Using the installed command-line script:
   ```bash
   cat-platformer
   ```

2. Using the executable script in the project root:
   ```bash
   ./cat_platformer_game.py
   ```

3. As a Python module:
   ```bash
   python -m cat_platformer
   ```

4. Running the main script directly:
   ```bash
   python cat_platformer_game.py
   ```

## Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver. Here's how to set up the project using uv:

1. Make sure you have Python 3.12 installed
2. Install uv if you don't have it already:
   ```bash
   curl -fsSL https://astral.sh/uv/install.sh | bash
   ```

3. Create a virtual environment in the project directory:
   ```bash
   uv venv --python=python3.12
   ```

4. Activate the virtual environment:
   - On Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```

5. Install dependencies from pyproject.toml:
   ```bash
   uv pip install -e .
   ```

6. Run the game:
   ```bash
   python cat_game.py
   ```

## Alternative Setup with pip

1. Make sure you have Python 3.12 installed
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
4. Install from pyproject.toml:
   ```bash
   pip install -e .
   ```
5. Run the game:
   ```bash
   python cat_game.py
   ```

## Development

This project uses a pyproject.toml file for dependency management and build configuration. The project has been switched from requirements.txt to pyproject.toml for better packaging and distribution.

You can install development dependencies with:

```bash
uv pip install -e ".[dev]"
```

To format and lint your code, you can use:

```bash
# Format with black
black cat_platformer

# Sort imports
isort cat_platformer

# Lint with flake8
flake8 cat_platformer
```

## Controls

- **Space**: Jump
- **R**: Restart game after game over

## Visibility Settings

The game has been optimized for visibility with:
- Bright, contrasting colors for the cat and obstacles
- Silhouetted foreground elements against the dusk sky
- Enhanced obstacle outlines for better gameplay visibility

## Game Mechanics

- Control a red cat on a platform
- Press space to jump over approaching obstacles
- Score increases for each obstacle you successfully avoid
- Game ends if you collide with an obstacle
- Press R to restart the game after a game over 